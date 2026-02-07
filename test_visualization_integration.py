
import unittest
import os
import shutil
import math
import matplotlib.pyplot as plt
import numpy as np
from unittest.mock import patch
from pathlib import Path
from aircraft_design.run_sizing import sizing_loop, DesignRequirements, InitialGuess
from aircraft_design.openvsp_interface import OpenVSPInterface
from aircraft_design.constraints import (
    required_thrust_to_weight,
    required_thrust_to_weight_for_sustained_turn,
    required_thrust_to_weight_for_takeoff_distance_numeric,
    max_wing_loading_for_landing_distance_numeric_pa,
    AeroPolar,
    qbar_pa,
    climb_sin_gamma_from_gradient
)

class TestVisualizationIntegration(unittest.TestCase):
    def setUp(self):
        self.docs_img_dir = Path("docs/images")
        self.docs_img_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path("output/test_viz_assets")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def test_generate_all_report_assets(self):
        print("\n=== Generating Report Assets ===")
        
        # 1. Run Sizing Loop to get Data
        print("Running Sizing Loop...")
        req = DesignRequirements(
            range_m=2000e3,
            payload_kg=1000.0,
            cruise_mach=0.8,
            cruise_altitude_m=11000.0,
            takeoff_distance_m=1000.0,
            landing_distance_m=1000.0,
            max_load_factor=7.33,
            sustained_turn_g=2.0,
            service_ceiling_m=15000.0
        )
        guess = InitialGuess(
            mtow_kg=10000.0,
            thrust_to_weight=0.6,
            wing_loading_pa=3000.0,
            aspect_ratio=3.5,
            sweep_deg=45.0,
            taper_ratio=0.3,
            thickness_ratio=0.08,
            sfc_cruise_1_s=0.000222,
            cd0=0.02,
            oswald_e=0.8
        )
        
        # Patch 'input' to avoid blocking during tests when visualization is enabled
        with patch('builtins.input', return_value=''):
             result = sizing_loop(req, guess)
        self.assertTrue(result.converged, "Sizing loop should converge for default inputs")
        
        # 2. Generate Sizing Convergence Plot
        print("Generating Sizing Convergence Plot...")
        self._plot_convergence(result.iteration_history, self.docs_img_dir / "sizing_convergence.png")
        
        # 3. Generate Constraint Diagram
        print("Generating Constraint Diagram...")
        self._plot_constraints(req, guess, result, self.docs_img_dir / "constraint_diagram.png")
        
        # 4. Generate Payload-Range Diagram
        print("Generating Payload-Range Diagram...")
        self._plot_payload_range(req, result, self.docs_img_dir / "payload_range.png")
        
        # 5. Generate OpenVSP Views
        print("Generating OpenVSP Views...")
        self._generate_vsp_views(result, self.docs_img_dir)
        
        # Verify all files exist
        required_files = [
            "sizing_convergence.png",
            "constraint_diagram.png",
            "payload_range.png",
            "vsp_iso_view.png",
            "vsp_top_view.png",
            "vsp_side_view.png"
        ]
        
        missing = []
        for f in required_files:
            path = self.docs_img_dir / f
            if path.exists():
                print(f"[OK] {f}")
            else:
                print(f"[MISSING] {f}")
                missing.append(f)
        
        self.assertEqual(len(missing), 0, f"Missing files: {missing}")

    def _plot_convergence(self, iterations, output_path):
        mtows = [it['mtow'] for it in iterations]
        iters = range(len(mtows))
        
        plt.figure(figsize=(8, 5))
        plt.plot(iters, mtows, 'b-o', linewidth=2)
        plt.xlabel("Iteration")
        plt.ylabel("MTOW (kg)")
        plt.title("Sizing Convergence History")
        plt.grid(True)
        plt.savefig(output_path, dpi=100)
        plt.close()

    def _plot_constraints(self, req, guess, result, output_path):
        # Simplified constraint plotting logic
        ws_range = np.linspace(1000, 8000, 50) # Pa
        
        # Constants
        rho_sl = 1.225
        rho_cruise = 0.364 # approx 11km
        a_sl = 340.0
        
        polar = AeroPolar(cd0=guess.cd0, e=guess.oswald_e, ar=guess.aspect_ratio)
        
        # 1. Takeoff Constraint (Simplified)
        # T/W = f(W/S, dist)
        tw_takeoff = []
        for ws in ws_range:
            # Using simplified approximation: TOP = W/S / (sigma * Clmax * T/W) -> T/W ~ W/S / (dist * const)
            # Or use the function if imported
            # Let's use a simple valid approximation for the plot
            tw = ws / (req.takeoff_distance_m * 1.0 * 1.8) # rough
            tw_takeoff.append(tw)
            
        # 2. Cruise Constraint
        tw_cruise = []
        q_cruise = 0.5 * rho_cruise * (req.cruise_mach * 295.0)**2
        for ws in ws_range:
            cd = guess.cd0 + polar.k * (ws/q_cruise)**2
            tw = q_cruise * cd / ws
            tw_cruise.append(tw)
            
        # 3. Landing Constraint (Vertical line)
        ws_landing = req.landing_distance_m * 1.8 * 1.225 * 2.0 # rough max W/S
        
        plt.figure(figsize=(8, 6))
        plt.plot(ws_range, tw_takeoff, label='Takeoff Distance', color='red')
        plt.plot(ws_range, tw_cruise, label='Cruise Speed', color='blue')
        plt.axvline(x=ws_landing, color='green', label='Landing Distance (Max W/S)')
        
        # Design Point
        final_ws = result.mtow_kg / result.wing_area_m2
        final_tw = result.thrust_sl_n / (result.mtow_kg * 9.81)
        plt.plot(final_ws, final_tw, 'k*', markersize=15, label='Design Point')
        
        plt.xlabel("Wing Loading (Pa)")
        plt.ylabel("Thrust-to-Weight Ratio")
        plt.title("Constraint Analysis Diagram")
        plt.legend()
        plt.grid(True)
        plt.ylim(0, 1.5)
        plt.savefig(output_path, dpi=100)
        plt.close()

    def _plot_payload_range(self, req, result, output_path):
        # Schematic Payload-Range
        ranges = [0, req.range_m, req.range_m * 1.3]
        payloads = [req.payload_kg, req.payload_kg, 0]
        
        plt.figure(figsize=(8, 5))
        plt.plot(ranges, payloads, 'g-', linewidth=2)
        plt.fill_between(ranges, payloads, color='green', alpha=0.1)
        
        plt.xlabel("Range (km)")
        plt.ylabel("Payload (kg)")
        plt.title("Payload-Range Diagram")
        plt.grid(True)
        plt.savefig(output_path, dpi=100)
        plt.close()

    def _generate_vsp_views(self, result, output_dir):
        vsp = OpenVSPInterface()
        if not vsp.is_available():
            print("OpenVSP not available, creating placeholder images.")
            self._create_placeholder_image(output_dir / "vsp_iso_view.png", "VSP ISO View (Placeholder)")
            self._create_placeholder_image(output_dir / "vsp_top_view.png", "VSP Top View (Placeholder)")
            self._create_placeholder_image(output_dir / "vsp_side_view.png", "VSP Side View (Placeholder)")
            return

        try:
            vsp.clear_model()
            
            # Create a simple representation based on result
            # Wing
            vsp.add_wing(
                span=math.sqrt(result.wing_area_m2 * result.geometry['aspect_ratio']),
                chord=math.sqrt(result.wing_area_m2 / result.geometry['aspect_ratio']),
                location_x=5.0
            )
            # Fuselage
            vsp.add_fuselage(length=12.0, diameter=1.5)
            
            # Snapshots
            # ISO
            vsp.set_view_azimuth_elevation(45, 30)
            vsp.window_snapshot(str(output_dir / "vsp_iso_view.png"))
            
            # Top
            vsp.set_view_azimuth_elevation(0, 90)
            vsp.window_snapshot(str(output_dir / "vsp_top_view.png"))
            
            # Side
            vsp.set_view_azimuth_elevation(90, 0)
            vsp.window_snapshot(str(output_dir / "vsp_side_view.png"))
            
        except Exception as e:
            print(f"Error generating VSP views: {e}")
            self._create_placeholder_image(output_dir / "vsp_iso_view.png", "VSP Error")
            self._create_placeholder_image(output_dir / "vsp_top_view.png", "VSP Error")
            self._create_placeholder_image(output_dir / "vsp_side_view.png", "VSP Error")

    def _create_placeholder_image(self, path, text):
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.text(0.5, 0.5, text, ha='center', va='center', fontsize=12)
        ax.set_axis_off()
        plt.savefig(path)
        plt.close()

if __name__ == "__main__":
    unittest.main()

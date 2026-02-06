from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .fixed_wing_overall import run_fixed_wing_overall_design
from .weights_structural import (
    calculate_wing_structural_weight,
    calculate_fuselage_structural_weight,
    calculate_horizontal_tail_structural_weight,
    calculate_vertical_tail_structural_weight,
    calculate_landing_gear_weight,
)
from .weights_system import (
    calculate_fuel_system_weight,
    calculate_propulsion_system_weight,
    calculate_flight_control_system_weight,
    calculate_avionics_weight,
    calculate_furnishings_weight,
)
from .propulsion import build_propulsion_model, thrust_available_n
from .performance import required_thrust_newton
from .mission import mission_fuel_breakdown
from .tail_sizing import tail_areas_from_volume_coefficients
from .sizing import wing_geometry_from_loading
from .units import CONST
from .constraints import AeroPolar
from .aero_drag_buildup import estimate_cd0_drag_buildup, GeometryAssumptions
from .aero_lift_slope import calculate_lift_induced_drag_factor
from .atmosphere import isa_tropopause


@dataclass
class DesignState:
    mtow_kg: float
    fuel_kg: float
    empty_weight_kg: float
    wing_area_m2: float
    thrust_sl_n: float
    component_weights: dict[str, float]
    geometry: dict[str, Any]
    performance_margins: dict[str, float]


class DesignOrchestrator:
    def __init__(self, initial_inputs: dict):
        self.inputs = copy.deepcopy(initial_inputs)
        self.history: list[DesignState] = []
        
    def run_initial_sizing(self) -> DesignState:
        """
        Run Class I sizing to get initial estimates.
        """
        # Run the existing Class I overall design
        res = run_fixed_wing_overall_design(self.inputs)
        
        # Extract results
        mtow_kg = res["weights"]["w0_kg"]
        fuel_kg = res["weights"]["wf_kg"]
        we_kg = res["weights"]["we_kg"]
        wing_area = res["sizing"]["wing_area_m2"]
        thrust_sl_n = res["sizing"]["thrust_sl_n"]
        
        # Initial geometry assumptions
        geometry = {
            "wing_area_m2": wing_area,
            "span_m": res["sizing"]["span_m"],
            "chord_mean_m": res["sizing"]["chord_mean_m"],
            "aspect_ratio": self.inputs["sizing"]["aspect_ratio"],
            # Default tail inputs if not present
            "ht_area_m2": res["stability"]["sh_m2"],
            "vt_area_m2": res["stability"]["sv_m2"],
            "fuselage_length_m": self.inputs["geometry_detailed"].get("fuselage", {}).get("length_m", 15.0),
        }
        
        state = DesignState(
            mtow_kg=mtow_kg,
            fuel_kg=fuel_kg,
            empty_weight_kg=we_kg,
            wing_area_m2=wing_area,
            thrust_sl_n=thrust_sl_n,
            component_weights={"class1_empty": we_kg},
            geometry=geometry,
            performance_margins={}
        )
        self.history.append(state)
        return state

    def run_detailed_sizing_loop(self, max_iter: int = 20, tol: float = 1e-3) -> DesignState:
        """
        Run Class II refined sizing loop.
        """
        current_state = self.history[-1]
        
        for i in range(max_iter):
            prev_mtow = current_state.mtow_kg
            
            # 1. Update Geometry based on current MTOW (maintain W/S and T/W)
            # Actually, usually we fix W/S and T/W from Constraint Analysis and scale the aircraft
            ws_pa = self.inputs["sizing"]["wing_loading_pa"]
            tw = self.inputs["sizing"]["thrust_to_weight"]
            
            new_wing_area = (current_state.mtow_kg * CONST.g0_m_s2) / ws_pa
            new_thrust_n = current_state.mtow_kg * CONST.g0_m_s2 * tw
            
            # Update span, chord
            ar = self.inputs["sizing"]["aspect_ratio"]
            new_span = (new_wing_area * ar)**0.5
            new_chord = new_wing_area / new_span
            
            # Update Tails (Volume coefficients)
            # L_t approx 0.45 * Fuselage Length? Or based on MAC?
            # Let's assume fuselage scales with MTOW? Or fixed?
            # For now, keep fuselage fixed unless specified.
            fus_len = current_state.geometry["fuselage_length_m"]
            
            # Recalculate tail areas
            tail_res = tail_areas_from_volume_coefficients(
                wing_area_m2=new_wing_area,
                mac_m=new_chord,
                span_m=new_span,
                fuselage_length_m=fus_len,
                vh=self.inputs.get("stability", {}).get("volume_coefficient_h", 0.9),
                vv=self.inputs.get("stability", {}).get("volume_coefficient_v", 0.06),
            )
            
            # 2. Calculate Component Weights (Class II)
            # Structural
            w_wing_res = calculate_wing_structural_weight(
                s_wing_m2=new_wing_area,
                aspect_ratio=ar,
                sweep_quarter_chord_deg=self.inputs["geometry_detailed"].get("wing", {}).get("sweep_deg", 0.0),
                taper_ratio=self.inputs["geometry_detailed"].get("wing", {}).get("taper_ratio", 0.5),
                max_takeoff_weight_kg=current_state.mtow_kg,
                n_limit=self.inputs["weights"].get("n_limit", 9.0),
                composite_fraction=self.inputs["weights"].get("composite_fraction_wing", 0.0),
            )
            
            w_fus_res = calculate_fuselage_structural_weight(
                fuselage_surface_area_m2=fus_len * 2.0, # Crude approx if detailed not avail
                max_takeoff_weight_kg=current_state.mtow_kg,
                fuselage_length_m=fus_len,
                n_limit=self.inputs["weights"].get("n_limit", 9.0),
                composite_fraction=self.inputs["weights"].get("composite_fraction_fuselage", 0.0),
            )
            
            w_ht_res = calculate_horizontal_tail_structural_weight(
                s_ht_m2=tail_res.sh_m2,
                max_takeoff_weight_kg=current_state.mtow_kg,
                composite_fraction=self.inputs["weights"].get("composite_fraction_tail", 0.0),
            )
            
            w_vt_res = calculate_vertical_tail_structural_weight(
                s_vt_m2=tail_res.sv_m2,
                max_takeoff_weight_kg=current_state.mtow_kg,
                composite_fraction=self.inputs["weights"].get("composite_fraction_tail", 0.0),
            )
            
            w_gear_res = calculate_landing_gear_weight(
                max_takeoff_weight_kg=current_state.mtow_kg,
                composite_fraction=self.inputs["weights"].get("composite_fraction_gear", 0.0),
            )
            
            # Systems
            w_fuel_sys_res = calculate_fuel_system_weight(
                fuel_weight_kg=current_state.fuel_kg,
            )
            
            # Estimate engine weight for propulsion system calc
            # Thrust = new_thrust_n
            # T/W_engine approx 6-8?
            # Let's use the build_propulsion_model to get a refined engine model if possible
            # Or just use the thrust scaling in calculate_propulsion_system_weight
            
            w_prop_res = calculate_propulsion_system_weight(
                thrust_sl_n=new_thrust_n,
                engine_count=self.inputs["propulsion"].get("engine_count", 1),
                fuselage_length_m=fus_len,
                has_afterburner=self.inputs["propulsion"].get("afterburner", True),
            )
            
            w_flight_ctrl_res = calculate_flight_control_system_weight(
                mtow_kg=current_state.mtow_kg,
                s_wing_m2=new_wing_area,
                b_wing_m=new_span,
                n_limit=self.inputs["weights"].get("n_limit", 9.0),
            )
            
            w_avionics_res = calculate_avionics_weight(
                mtow_kg=current_state.mtow_kg,
                w_engine_kg=w_prop_res.details.get("w_engine_dry_lb_per", 0.0) * 0.453592, # Approximate back
                num_engines=self.inputs["propulsion"].get("engine_count", 1),
                w_fuel_system_kg=w_fuel_sys_res.w_system_kg,
            )
            
            w_furnish_res = calculate_furnishings_weight(
                mtow_kg=current_state.mtow_kg,
                q_dive_pa=self.inputs["mission"].get("q_dive_pa", 50000.0), # Default high q
                num_crew=self.inputs["crew"].get("count", 1),
            )
            
            # Sum Empty Weight
            new_empty_kg = (
                w_wing_res.w_structural_kg +
                w_fus_res.w_structural_kg +
                w_ht_res.w_structural_kg +
                w_vt_res.w_structural_kg +
                w_gear_res.w_structural_kg +
                w_fuel_sys_res.w_system_kg +
                w_prop_res.w_system_kg +
                w_flight_ctrl_res.w_system_kg +
                w_avionics_res.w_system_kg +
                w_furnish_res.w_system_kg
            )
            
            # 3. Update Fuel (Mission)
            # Re-calculate fuel fraction based on refined drag and propulsion model
            
            # Build Propulsion Model
            prop_model = build_propulsion_model(self.inputs["propulsion"])
            
            # Build Geometry Assumptions for Drag
            # We approximate detailed geometry from current sizing
            fus_diam = self.inputs["geometry_detailed"].get("fuselage", {}).get("diameter_m", fus_len / 10.0)
            
            geo_assumptions = GeometryAssumptions(
                fuselage_length_m=fus_len,
                fuselage_diameter_m=fus_diam,
                wetted_area_factor=self.inputs["aero"].get("wetted_area_factor", 3.0),
                wing_t_c=self.inputs["geometry_detailed"].get("wing", {}).get("thickness_ratio", 0.12),
                tail_area_ratio=0.25, # Fallback
                htail_area_ratio=tail_res.sh_m2 / new_wing_area,
                vtail_area_ratio=tail_res.sv_m2 / new_wing_area,
                htail_t_c=self.inputs["geometry_detailed"].get("tail", {}).get("thickness_ratio", 0.10),
                vtail_t_c=self.inputs["geometry_detailed"].get("tail", {}).get("thickness_ratio", 0.10),
            )
            
            # Estimate CD0
            # Need cruise conditions from mission input or constraints
            cruise_alt = self.inputs["mission"].get("cruise_altitude_m", 10000.0)
            cruise_mach = self.inputs["mission"].get("cruise_mach", 0.78)
            
            atm = isa_tropopause(cruise_alt)
            cruise_speed = cruise_mach * atm.a_m_s
            
            drag_res = estimate_cd0_drag_buildup(
                cruise_altitude_m=cruise_alt,
                cruise_speed_m_s=cruise_speed,
                s_ref_m2=new_wing_area,
                b_m=new_span,
                cbar_m=new_chord,
                assumptions=geo_assumptions,
            )
            
            # Induced Drag Factor k
            k_factor = calculate_lift_induced_drag_factor(
                aspect_ratio=ar,
                taper_ratio=self.inputs["geometry_detailed"].get("wing", {}).get("taper_ratio", 0.5),
                sweep_quarter_chord_deg=self.inputs["geometry_detailed"].get("wing", {}).get("sweep_deg", 0.0),
            )
            
            # Build Polar
            polar = AeroPolar(
                cd0=drag_res.cd0,
                k=k_factor,
                cl_max=self.inputs["aero"].get("cl_max_clean", 1.5),
                cl_min=-0.5
            )
            
            # Run Mission Analysis
            mission_res = mission_fuel_breakdown(
                w0_kg=current_state.mtow_kg, # Use previous iteration's MTOW for drag calc
                s_m2=new_wing_area,
                polar=polar,
                propulsion=prop_model,
                mission=self.inputs["mission"],
            )
            
            fuel_fraction = mission_res["fuel_fraction_total"]
            
            # Recalculate Weights with new fuel fraction
            # W0 = (We + W_pay + W_crew) / (1 - fuel_fraction)
            # Ensure fuel_fraction is reasonable (< 1.0)
            if fuel_fraction >= 0.95:
                 fuel_fraction = 0.95 # Limit to prevent explosion
            
            new_fuel_kg = fuel_fraction * (new_empty_kg + self.inputs["payload"]["payload_kg"] + self.inputs["crew"]["crew_kg"]) / (1.0 - fuel_fraction)
            
            # Update MTOW
            new_mtow_kg = new_empty_kg + new_fuel_kg + self.inputs["payload"]["payload_kg"] + self.inputs["crew"]["crew_kg"]
            
            # Check convergence
            diff = abs(new_mtow_kg - prev_mtow)
            
            # Update State
            current_state = DesignState(
                mtow_kg=new_mtow_kg,
                fuel_kg=new_fuel_kg,
                empty_weight_kg=new_empty_kg,
                wing_area_m2=new_wing_area,
                thrust_sl_n=new_thrust_n,
                component_weights={
                    "wing": w_wing_res.w_structural_kg,
                    "fuselage": w_fus_res.w_structural_kg,
                    "ht": w_ht_res.w_structural_kg,
                    "vt": w_vt_res.w_structural_kg,
                    "gear": w_gear_res.w_structural_kg,
                    "fuel_system": w_fuel_sys_res.w_system_kg,
                    "propulsion": w_prop_res.w_system_kg,
                    "flight_control": w_flight_ctrl_res.w_system_kg,
                    "avionics": w_avionics_res.w_system_kg,
                    "furnishings": w_furnish_res.w_system_kg,
                },
                geometry={
                    "wing_area_m2": new_wing_area,
                    "span_m": new_span,
                    "chord_mean_m": new_chord,
                    "aspect_ratio": ar,
                    "ht_area_m2": tail_res.sh_m2,
                    "vt_area_m2": tail_res.sv_m2,
                    "fuselage_length_m": fus_len,
                },
                performance_margins={
                    "cd0": drag_res.cd0,
                    "k": k_factor,
                    "l_d_cruise": 1.0 / (2.0 * (drag_res.cd0 * k_factor)**0.5), # Approx max L/D
                    "mission_fuel_fraction": fuel_fraction,
                }
            )
            self.history.append(current_state)
            
            if diff < tol * prev_mtow:
                break
                
        return current_state


import time
import math
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aircraft_design.visualization_realtime import RealTimeVisualizer
from aircraft_design.openvsp_interface import OpenVSPInterface

def test_vsp_interface():
    print("Testing OpenVSP Interface...")
    vsp = OpenVSPInterface()
    if vsp.is_available():
        print("VSP Available. Clearing model...")
        vsp.clear_model()
        print("Adding Fuselage...")
        fid = vsp.add_fuselage(10.0, 1.2)
        print(f"Fuselage ID: {fid}")
        print("Adding Wing...")
        wid = vsp.add_wing(20.0, 10.0, 4.0)
        print(f"Wing ID: {wid}")
        
        outfile = "test_aircraft.vsp3"
        print(f"Exporting to {outfile}...")
        vsp.export_file(outfile)
        if os.path.exists(outfile):
            print("Export successful.")
            # os.remove(outfile) # Keep for inspection
        else:
            print("Export failed.")
    else:
        print("VSP Not Available (Expected in this env due to library loading policy).")

def test_viz_and_generate_report_assets():
    print("Testing Visualization & Generating Report Assets...")
    viz = RealTimeVisualizer()
    viz.start()
    
    # Simulate a design loop
    max_iter = 20
    print("Running loop...")
    for i in range(max_iter):
        # Fake convergence data
        # MTOW converges to 10000
        mtow = 10000 + 5000 * math.exp(-i/5.0)
        if i > 0:
            error = abs(mtow - (10000 + 5000 * math.exp(-(i-1)/5.0))) / mtow
        else:
            error = 1.0
            
        viz.update_iteration(i, mtow, error)
        
        # Fake constraints update (once)
        if i == 0:
            viz.update_constraints(
                constraints_data={
                    'ws_range': list(range(100, 600, 10)),
                    'takeoff': [0.2 + 0.001 * x for x in range(100, 600, 10)],
                    'landing': 450,
                    'climb': [0.3 for _ in range(100, 600, 10)],
                    'turn': [0.4 + 0.0005 * x for x in range(100, 600, 10)]
                },
                design_point={'ws': 400, 'tw': 0.45}
            )
            
        time.sleep(0.1) # Fast simulation
    
    # Save image for report
    # The report expects: output/plots/convergence_example.png
    output_path = os.path.abspath("output/plots/convergence_example.png")
    print(f"Saving report image to: {output_path}")
    viz.save_screenshot(output_path)
    
    # Give it a moment to save
    time.sleep(2.0)
    
    if os.path.exists(output_path):
        print(f"[SUCCESS] Image generated at {output_path}")
    else:
        print(f"[FAILURE] Image not found at {output_path}")

    print("Visualization demo done. Closing...")
    viz.stop()
    print("Visualization closed.")

if __name__ == "__main__":
    test_vsp_interface()
    test_viz_and_generate_report_assets()

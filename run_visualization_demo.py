import time
import math
import random
from aircraft_design.visualization_realtime import RealTimeVisualizer
import multiprocessing

def run_demo():
    print("Starting Real-Time Visualization Demo...")
    
    # Initialize Visualizer
    viz = RealTimeVisualizer()
    viz.start()
    
    try:
        # Simulate a design loop
        max_iterations = 50
        
        # Initial Design Point
        mtow = 50000.0
        error = 1.0
        
        for i in range(max_iterations):
            # Simulate optimization progress
            # MTOW converges to ~45000
            target_mtow = 45000.0
            mtow = mtow - (mtow - target_mtow) * 0.1 + random.uniform(-100, 100)
            error = error * 0.85
            if error < 1e-6: error = 1e-6
            
            # Create dummy geometry update
            # Expanding wing span slightly
            span = 30.0 + i * 0.05
            geom = {
                'fuselage': {'length_m': 35.0, 'diameter_m': 3.5},
                'wing': {'s_ref_m2': 120.0, 'aspect_ratio': span**2/120.0}
            }
            
            # Send update
            viz.update_iteration(i, mtow, error, geometry=geom)
            
            # Send constraints every 10 iterations
            if i % 10 == 0:
                ws_range = [3000 + x*100 for x in range(50)]
                constraints = {
                    'ws_range': ws_range,
                    'takeoff': [0.2 + 0.00005 * ws for ws in ws_range],
                    'landing': 6000, # Max WS
                    'turn': [0.3 + 0.00002 * ws for ws in ws_range],
                    'climb': [0.15 for _ in ws_range]
                }
                design_point = {'ws': 5500, 'tw': 0.35}
                viz.update_constraints(constraints, design_point)

            # Send Payload-Range update at the end or periodically
            if i == max_iterations - 1:
                # Range in km
                ranges_km = [0, 5000, 6500]
                payloads = [20000, 20000, 0]
                viz.update_payload_range(ranges_km, payloads)
            
            print(f"Iteration {i}: MTOW={mtow:.1f}, Error={error:.2e}")
            time.sleep(0.2) # Simulate calculation time
            
        print("Optimization Converged.")
        print("Keep window open for 10 seconds...")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("Demo interrupted.")
    finally:
        print("Stopping visualizer...")
        viz.stop()
        print("Done.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_demo()

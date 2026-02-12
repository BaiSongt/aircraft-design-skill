# Mock OpenFOAM Solver
# This script simulates the behavior of a real CFD solver for testing purposes.
# It prints out lines that mimic the residual output of OpenFOAM.

import time
import random
import sys

def main():
    print("Starting Mock Solver...")

    # Initial residuals
    residuals = {
        'Ux': 0.1,
        'Uy': 0.1,
        'p': 0.1,
        'k': 0.1,
    }

    # Simulate 20 time steps
    for i in range(1, 21):
        print(f"Time = {i}")

        # Update residuals with some randomness
        for key in residuals:
            # Print initial residual for the sub-iteration
            print(f"    Solving for {key}, Initial residual = {residuals[key]:.6f}, ...")

            # Decrease residual
            residuals[key] *= random.uniform(0.6, 0.9)

            # Print final residual
            print(f"    ExecutionTime = {i * 0.1:.2f} s  ClockTime = {i * 0.1:.2f} s")

        # Occasionally print a line that is NOT a residual
        if i % 5 == 0:
            print("Courant Number mean: 0.2 max: 0.5")

        # Flush stdout to ensure the monitoring script can read it in real-time
        sys.stdout.flush()
        time.sleep(0.5)

    print("End")
    print("Mock Solver Finished Successfully.")

if __name__ == "__main__":
    main()

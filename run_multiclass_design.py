# refact/run_multiclass_design.py
import argparse
import json
from pathlib import Path
from datetime import datetime
import os
import sys

# Ensure the refact directory is on the path
# This allows running the script from the original root directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from aircraft_design.class1_conceptual import execute_stage as execute_class1
from aircraft_design.class2_preliminary import execute_stage as execute_class2
from aircraft_design.class3_detailed import execute_stage as execute_class3


def setup_output_directory(base_dir: str = "output", project_name: str = "design") -> Path:
    """Creates a timestamped output directory for the current run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{project_name}_{timestamp}"
    output_path = Path(base_dir) / dir_name
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Run Multi-Class Aircraft Design Workflow")
    parser.add_argument("input_file", type=Path, help="Path to the master input JSON file")
    parser.add_argument("--project-name", "-n", type=str, default="multiclass_design", help="Name of the project")
    parser.add_argument("--output-dir", "-o", type=Path, default=Path("output"), help="Base directory for outputs")
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} not found.")
        sys.exit(1)

    # 1. Setup main output directory
    run_dir = setup_output_directory(args.output_dir, args.project_name)
    print(f"🚀 Starting Multi-Class Design Workflow. Outputs will be in: {run_dir}")

    # Load master input data
    with open(args.input_file, "r") as f:
        master_input_data = json.load(f)

    # =================================================================================
    # STAGE 1: Conceptual Design (Class I)
    # =================================================================================
    print("\n" + "="*25 + " STAGE 1: CLASS I (Conceptual) " + "="*25)
    class1_dir = run_dir / "class1"
    class1_dir.mkdir()
    class1_output_path = execute_class1(master_input_data, class1_dir)
    print(f"✅ Class I analysis complete. Results in: {class1_output_path}")

    # Load Class I results to feed into Class II
    with open(class1_output_path, "r") as f:
        class1_results = json.load(f)

    # =================================================================================
    # STAGE 2: Preliminary Design (Class II)
    # =================================================================================
    print("\n" + "="*25 + " STAGE 2: CLASS II (Preliminary) " + "="*25)
    class2_dir = run_dir / "class2"
    class2_dir.mkdir()
    # Pass the full results from Class I as the input for Class II
    class2_output_path = execute_class2(class1_results, class2_dir)
    print(f"✅ Class II analysis complete. Results in: {class2_output_path}")

    # Load Class II results to feed into Class III
    with open(class2_output_path, "r") as f:
        class2_results = json.load(f)

    # =================================================================================
    # STAGE 3: Detailed Analysis (Class III)
    # =================================================================================
    print("\n" + "="*25 + " STAGE 3: CLASS III (Detailed) " + "="*25)
    class3_dir = run_dir / "class3"
    class3_dir.mkdir()
    # Pass the full results from Class II as the input for Class III
    class3_output_path = execute_class3(class2_results, class3_dir)
    print(f"✅ Class III analysis complete. Results in: {class3_output_path}")

    print("\n🎉 Multi-Class Design Workflow finished successfully!")


if __name__ == "__main__":
    main()

# refact/tests/test_multiclass_workflow.py
import json
from pathlib import Path
from unittest.mock import patch
import pytest

# This assumes that pytest is run from the root of the 'refact' directory,
# so the directory is added to the path.
from run_multiclass_design import main as multiclass_main

@pytest.fixture
def sample_input_file(tmp_path: Path) -> Path:
    """Creates a sample master input file for the workflow."""
    input_data = {
        "requirements": {
            "range_m": 1.5e6,
            "payload_kg": 800.0,
            "cruise_mach": 0.7,
            "cruise_altitude_m": 9000.0
        },
        "mission": {
            "fuel_fraction_class1": 0.35
        },
        "payload": {
            "payload_kg": 800.0
        },
        "crew": {
            "crew_kg": 160
        },
        "weights": {
            "empty_a": 0.97,
            "empty_b": 0.06,
            "reserve_fraction": 0.05,
            "w0_guess_kg": 8000
        },
        "initial_guess": {
             "thrust_to_weight": 0.5,
             "wing_loading_pa": 2800.0
        }
    }
    input_file = tmp_path / "master_input.json"
    input_file.write_text(json.dumps(input_data))
    return input_file


def test_multiclass_workflow_e2e(sample_input_file: Path, tmp_path: Path):
    """
    End-to-end test for the new multi-class design workflow.
    Verifies that the main script runs and creates the expected directory structure.
    """
    output_dir = tmp_path / "test_output"
    project_name = "E2E_Test"

    # Mock sys.argv to run the main script
    test_args = [
        "run_multiclass_design.py",
        str(sample_input_file),
        "--output-dir",
        str(output_dir),
        "--project-name",
        project_name,
    ]

    with patch("sys.argv", test_args):
        try:
            multiclass_main()
        except SystemExit as e:
            # A SystemExit with code 0 or None is a clean exit
            assert e.code == 0 or e.code is None, f"Script exited with error code {e.code}"

    # --- Verification ---
    # Find the timestamped run directory
    run_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith(project_name)]
    assert len(run_dirs) == 1, "Expected exactly one run directory to be created"
    run_dir = run_dirs[0]

    # Check for class-specific subdirectories
    class1_dir = run_dir / "class1"
    class2_dir = run_dir / "class2"
    class3_dir = run_dir / "class3"

    assert class1_dir.is_dir(), "Class 1 output directory not created"
    assert class2_dir.is_dir(), "Class 2 output directory not created"
    assert class3_dir.is_dir(), "Class 3 output directory not created"

    # Check for output files
    class1_output = class1_dir / "class1_output.json"
    class2_output = class2_dir / "class2_output.json"
    class3_output = class3_dir / "class3_output.json"
    
    assert class1_output.exists(), "Class 1 JSON output not found"
    assert class2_output.exists(), "Class 2 JSON output not found"
    assert class3_output.exists(), "Class 3 JSON output not found"

    # Verify content chaining (Class 1 -> Class 2)
    with open(class1_output) as f:
        class1_data = json.load(f)
    with open(class2_output) as f:
        class2_data = json.load(f)

    # Check that the input for class 2 was the output of class 1
    assert class2_data["inputs"] == class1_data
    
    # Check that Class 1 produced a valid MTOW guess for Class 2
    mtow_from_c1 = class1_data["initial_guess"]["mtow_kg"]
    assert isinstance(mtow_from_c1, (int, float))
    assert mtow_from_c1 > 0

    print(f"Workflow test passed successfully. Outputs in {run_dir}")


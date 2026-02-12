import json
from pathlib import Path
from unittest.mock import patch

from aircraft_design.class2_preliminary.run_sizing import main as run_sizing_main


def _run_sizing_with_input(input_path: Path, output_dir: Path, project_name: str) -> Path:
    args = [
        "run_sizing.py",
        str(input_path),
        "--output-dir",
        str(output_dir),
        "--project-name",
        project_name,
        "--no-viz",
    ]
    with patch("sys.argv", args):
        try:
            run_sizing_main()
        except SystemExit as e:
            assert e.code == 0 or e.code is None

    run_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith(project_name)]
    assert len(run_dirs) == 1
    return run_dirs[0]


def _assert_basic_outputs(run_dir: Path):
    assert (run_dir / "design_data.json").exists()
    assert (run_dir / "design_report.md").exists()
    assert (run_dir / "interactive_charts.html").exists()


def test_workflow_automation_for_current_inputs(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    sizing_input = repo_root / "sizing_input.json"
    adv_input = repo_root / "sizing_input_advanced.json"

    assert sizing_input.exists()
    assert adv_input.exists()

    output_dir = tmp_path / "output"

    run_dir_basic = _run_sizing_with_input(sizing_input, output_dir, "WorkflowBasic")
    _assert_basic_outputs(run_dir_basic)

    run_dir_adv = _run_sizing_with_input(adv_input, output_dir, "WorkflowAdvanced")
    _assert_basic_outputs(run_dir_adv)

    with open(run_dir_adv / "design_data.json", encoding="utf-8") as f:
        data = json.load(f)
    if data["outputs"]["converged"]:
        roadmap = run_dir_adv / "technical_roadmap_report.md"
        assert roadmap.exists()

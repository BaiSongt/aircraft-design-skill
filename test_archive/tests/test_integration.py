import pytest
import os
import json
import shutil
from pathlib import Path
from aircraft_design.run_sizing import main as run_sizing_main
from unittest.mock import patch

def test_full_integration_flow(tmp_path):
    """TC06: End-to-end integration test from JSON input to Report generation."""
    
    # Setup input file
    input_data = {
        "requirements": {
            "range_m": 1000000.0,
            "payload_kg": 500.0,
            "cruise_mach": 0.6,
            "cruise_altitude_m": 8000.0
        },
        "initial_guess": {
            "mtow_kg": 5000.0
        }
    }
    
    input_file = tmp_path / "test_input.json"
    with open(input_file, "w") as f:
        json.dump(input_data, f)
        
    output_dir = tmp_path / "output"
    
    # Mock sys.argv
    test_args = ["run_sizing.py", str(input_file), "--output-dir", str(output_dir), "--project-name", "TestProject"]
    
    with patch("sys.argv", test_args):
        try:
            run_sizing_main()
        except SystemExit as e:
            assert e.code == 0 or e.code is None
            
    # Check outputs
    # Since timestamp is in dir name, we need to find the created dir
    dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("TestProject")]
    assert len(dirs) == 1
    run_dir = dirs[0]
    
    assert (run_dir / "design_data.json").exists()
    assert (run_dir / "design_report.md").exists()
    assert (run_dir / "interactive_charts.html").exists()
    
    # Verify content
    with open(run_dir / "design_data.json") as f:
        data = json.load(f)
        assert data["outputs"]["converged"] is True
        
    with open(run_dir / "design_report.md") as f:
        report = f.read()
        assert "# 飞机总体设计报告" in report
        assert "## 5. 重量与重心分析" in report # Check for new section
        
def test_performance_sla():
    """TC07: Performance test - Sizing loop should be fast."""
    import time
    from aircraft_design.design_loop_orchestrator import sizing_loop, DesignRequirements, InitialGuess
    
    req = DesignRequirements(
        range_m=2000e3, 
        payload_kg=1000.0, 
        cruise_mach=0.8, 
        cruise_altitude_m=11000.0,
        takeoff_distance_m=1500.0,
        landing_distance_m=1500.0
    )
    guess = InitialGuess(
        mtow_kg=10000.0,
        wing_loading_pa=3000.0,
        thrust_to_weight=0.5
    )
    
    start_time = time.time()
    for _ in range(5): # Run 5 times to average
        sizing_loop(req, guess)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 5.0
    print(f"Average sizing loop time: {avg_time:.4f}s")
    
    # SLA: < 5.0 seconds (relaxed for test environment)
    assert avg_time < 5.0

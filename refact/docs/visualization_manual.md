# Real-Time Visualization Module Manual

## Overview
The Real-Time Visualization Module provides dynamic feedback during the aircraft sizing and optimization process. It runs in a separate process to avoid blocking the main design loop, utilizing **PySide6 (Qt)** for a responsive and modern user interface.

## Features
- **Convergence History**: Real-time plot of MTOW and Relative Error vs Iteration.
- **Constraint Analysis**: Dynamic constraint diagram showing feasible design space and current design point.
- **3D Geometry**: Interactive 3D visualization of the aircraft geometry (Fuselage + Wing).
- **Interactive Controls**:
  - **Pause/Resume**: Pause the visualization updates.
  - **Save Image**: Save a snapshot of the current view.
  - **Export CSV**: Export the convergence history to a CSV file.
  - **Reset View**: Reset the plot axes to fit the data.

## Usage

### Integration
To use the visualizer in your code:

```python
from aircraft_design.visualization_realtime import RealTimeVisualizer

# 1. Initialize and Start
viz = RealTimeVisualizer()
viz.start()

try:
    # 2. Update inside your loop
    viz.update_iteration(
        iteration=i, 
        mtow=current_mtow, 
        error=current_error,
        geometry=current_geometry_dict # Optional
    )
    
    # 3. Update constraints (less frequent)
    viz.update_constraints(constraints_data, design_point)
    
finally:
    # 4. Ensure cleanup
    viz.stop()
```

### UI Controls
- **Pause/Resume**: Toggles data processing. Note that the background process continues to receive data, but the plot will not update until resumed.
- **Save Image**: Saves `viz_snapshot_YYYYMMDD_HHMMSS.png` in the current directory.
- **Export CSV**: Saves `design_history_YYYYMMDD_HHMMSS.csv` containing Iteration, MTOW, and Error data.
- **Reset View**: Re-scales all axes to fit the current data range.

## Architecture
The module uses `multiprocessing` to run the GUI in a separate process. Data is passed via `multiprocessing.Queue`.

- `RealTimeVisualizer`: The main interface class (runs in main process).
- `VisualizationProcess`: The background process class (launches the PySide6 application).
- `MainWindow`: The main GUI window implemented in PySide6.

## Dependencies
- `PySide6`
- `matplotlib`
- `numpy`

## Verification and Testing

### Integration Test
A comprehensive integration test script is provided to verify the visualization module and report asset generation:

```bash
python3 test_visualization_integration.py
```

This script performs the following:
1.  Runs the `sizing_loop` with default parameters.
2.  Generates static plots (Convergence, Constraints, Payload-Range) using the simulation data.
3.  Attempts to generate OpenVSP views (creates placeholders if OpenVSP is not available).
4.  Verifies that all required images for `technical_roadmap_report.md` are created in `docs/images/`.

### Report Validation
To ensure that the generated images are correctly referenced in the documentation:

```bash
python3 check_doc_images.py
```

This utility scans `technical_roadmap_report.md` for image references and verifies their existence on disk.

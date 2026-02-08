from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .geometry_modeling import AircraftGeometry


@dataclass(frozen=True)
class VSPAEROResult:
    cl: float
    cd: float
    cm: float
    cn: float
    cy: float
    cl_alpha: float
    cd_alpha: float
    lift_distribution: dict
    drag_distribution: dict
    moment_coefficients: dict


def generate_vspaero_input(
    *,
    geometry: AircraftGeometry,
    output_file: str,
    mach: float = 0.7,
    alpha_deg: float = 0.0,
    beta_deg: float = 0.0,
    num_spanwise: int = 20,
    num_chordwise: int = 10,
) -> None:
    if mach <= 0.0:
        raise ValueError("mach must be positive.")
    if output_file is None or output_file == "":
        raise ValueError("output_file must be specified.")

    with open(output_file, "w") as f:
        f.write("VSPAERO INPUT FILE\n")
        f.write("====================\n\n")

        f.write(f"$MACH {mach:.6f}\n")
        f.write(f"$ALPHA {alpha_deg:.6f}\n")
        f.write(f"$BETA {beta_deg:.6f}\n")
        f.write(f"$NUMSPANWISE {num_spanwise}\n")
        f.write(f"$NUMCHORDWISE {num_chordwise}\n\n")

        f.write("$GEOM\n")
        f.write("WING\n")
        f.write(f"  {geometry.wing.area:.6f}\n")
        f.write(f"  {geometry.wing.span:.6f}\n")
        f.write(f"  {geometry.wing.chord_root:.6f}\n")
        f.write(f"  {geometry.wing.chord_tip:.6f}\n")
        f.write(f"  {geometry.wing.sweep_quarter_chord:.6f}\n")
        f.write(f"  {geometry.wing.taper_ratio:.6f}\n")
        f.write(f"  {geometry.wing.twist_root:.6f}\n")
        f.write(f"  {geometry.wing.twist_tip:.6f}\n")
        f.write(f"  {geometry.wing.dihedral:.6f}\n")
        f.write(f"  {geometry.wing.incidence:.6f}\n")
        f.write(f"  {geometry.wing.airfoil_root}\n")
        f.write(f"  {geometry.wing.airfoil_tip}\n")
        f.write(f"  {geometry.wing.position[0]:.6f} {geometry.wing.position[1]:.6f} {geometry.wing.position[2]:.6f}\n")

        f.write("FUSELAGE\n")
        f.write(f"  {geometry.fuselage.length:.6f}\n")
        f.write(f"  {geometry.fuselage.diameter:.6f}\n")
        f.write(f"  {geometry.fuselage.fineness_ratio:.6f}\n")
        f.write(f"  {geometry.fuselage.nose_length:.6f}\n")
        f.write(f"  {geometry.fuselage.tail_length:.6f}\n")
        f.write(
            f"  {geometry.fuselage.position[0]:.6f} {geometry.fuselage.position[1]:.6f} {geometry.fuselage.position[2]:.6f}\n"
        )

        f.write("HTAIL\n")
        f.write(f"  {geometry.h_tail.area:.6f}\n")
        f.write(f"  {geometry.h_tail.span:.6f}\n")
        f.write(f"  {geometry.h_tail.chord_root:.6f}\n")
        f.write(f"  {geometry.h_tail.chord_tip:.6f}\n")
        f.write(f"  {geometry.h_tail.sweep_quarter_chord:.6f}\n")
        f.write(f"  {geometry.h_tail.taper_ratio:.6f}\n")
        f.write(f"  {geometry.h_tail.incidence:.6f}\n")
        f.write(f"  {geometry.h_tail.airfoil}\n")
        f.write(
            f"  {geometry.h_tail.position[0]:.6f} {geometry.h_tail.position[1]:.6f} {geometry.h_tail.position[2]:.6f}\n"
        )

        f.write("VTAIL\n")
        f.write(f"  {geometry.v_tail.area:.6f}\n")
        f.write(f"  {geometry.v_tail.span:.6f}\n")
        f.write(f"  {geometry.v_tail.chord_root:.6f}\n")
        f.write(f"  {geometry.v_tail.chord_tip:.6f}\n")
        f.write(f"  {geometry.v_tail.sweep_quarter_chord:.6f}\n")
        f.write(f"  {geometry.v_tail.taper_ratio:.6f}\n")
        f.write(f"  {geometry.v_tail.airfoil}\n")
        f.write(
            f"  {geometry.v_tail.position[0]:.6f} {geometry.v_tail.position[1]:.6f} {geometry.v_tail.position[2]:.6f}\n"
        )

        for i, engine in enumerate(geometry.engines):
            f.write(f"ENGINE {i + 1}\n")
            f.write(f"  {engine.diameter:.6f}\n")
            f.write(f"  {engine.length:.6f}\n")
            f.write(f"  {engine.bypass_ratio:.6f}\n")
            f.write(f"  {engine.position[0]:.6f} {engine.position[1]:.6f} {engine.position[2]:.6f}\n")
            f.write(f"  {engine.orientation[0]:.6f} {engine.orientation[1]:.6f} {engine.orientation[2]:.6f}\n")

        for i, gear in enumerate(geometry.landing_gear):
            f.write(f"LANDING_GEAR {i + 1}\n")
            f.write(f"  {gear.type}\n")
            f.write(f"  {gear.position[0]:.6f} {gear.position[1]:.6f} {gear.position[2]:.6f}\n")
            f.write(f"  {gear.height:.6f}\n")
            f.write(f"  {gear.track_width:.6f}\n")

        f.write("$END\n")


def parse_vspaero_output(
    *,
    output_file: str,
) -> VSPAEROResult:
    cl = 0.0
    cd = 0.0
    cm = 0.0
    cn = 0.0
    cy = 0.0
    cl_alpha = 0.0
    cd_alpha = 0.0
    lift_distribution = {}
    drag_distribution = {}
    moment_coefficients = {}

    with open(output_file, "r") as f:
        for line in f:
            if line.startswith("CL"):
                cl = float(line.split()[1])
            elif line.startswith("CD"):
                cd = float(line.split()[1])
            elif line.startswith("CM"):
                cm = float(line.split()[1])
            elif line.startswith("CN"):
                cn = float(line.split()[1])
            elif line.startswith("CY"):
                cy = float(line.split()[1])
            elif line.startswith("CLALPHA"):
                cl_alpha = float(line.split()[1])
            elif line.startswith("CDALPHA"):
                cd_alpha = float(line.split()[1])
            elif line.startswith("LIFT_DISTRIBUTION"):
                parts = line.split()
                spanwise_location = float(parts[1])
                lift_value = float(parts[2])
                lift_distribution[spanwise_location] = lift_value
            elif line.startswith("DRAG_DISTRIBUTION"):
                parts = line.split()
                spanwise_location = float(parts[1])
                drag_value = float(parts[2])
                drag_distribution[spanwise_location] = drag_value
            elif line.startswith("MOMENT_COEFF"):
                parts = line.split()
                moment_type = parts[1]
                moment_value = float(parts[2])
                moment_coefficients[moment_type] = moment_value

    return VSPAEROResult(
        cl=cl,
        cd=cd,
        cm=cm,
        cn=cn,
        cy=cy,
        cl_alpha=cl_alpha,
        cd_alpha=cd_alpha,
        lift_distribution=lift_distribution,
        drag_distribution=drag_distribution,
        moment_coefficients=moment_coefficients,
    )


def calculate_lift_distribution(
    *,
    vspaero_results: VSPAEROResult,
    geometry: AircraftGeometry,
) -> dict:
    spanwise_locations = list(vspaero_results.lift_distribution.keys())
    lift_values = list(vspaero_results.lift_distribution.values())

    spanwise_locations_normalized = [
        (loc - geometry.wing.position[0]) / geometry.wing.span for loc in spanwise_locations
    ]

    distribution = {
        "spanwise_location": spanwise_locations,
        "spanwise_location_normalized": spanwise_locations_normalized,
        "lift_coefficient": lift_values,
        "total_lift": sum(lift_values),
    }

    return distribution


def calculate_drag_distribution(
    *,
    vspaero_results: VSPAEROResult,
    geometry: AircraftGeometry,
) -> dict:
    spanwise_locations = list(vspaero_results.drag_distribution.keys())
    drag_values = list(vspaero_results.drag_distribution.values())

    spanwise_locations_normalized = [
        (loc - geometry.wing.position[0]) / geometry.wing.span for loc in spanwise_locations
    ]

    distribution = {
        "spanwise_location": spanwise_locations,
        "spanwise_location_normalized": spanwise_locations_normalized,
        "drag_coefficient": drag_values,
        "total_drag": sum(drag_values),
    }

    return distribution


def calculate_moment_coefficients(
    *,
    vspaero_results: VSPAEROResult,
) -> dict:
    return {
        "pitch_moment": vspaero_results.moment_coefficients.get("CM", 0.0),
        "roll_moment": vspaero_results.moment_coefficients.get("CR", 0.0),
        "yaw_moment": vspaero_results.moment_coefficients.get("CY", 0.0),
    }


def run_vspaero_analysis(
    *,
    geometry: AircraftGeometry,
    mach: float = 0.7,
    alpha_deg: float = 0.0,
    output_file: str = "vspaero_output.txt",
    input_file: str = "vspaero_input.txt",
) -> VSPAEROResult:
    generate_vspaero_input(
        geometry=geometry,
        output_file=input_file,
        mach=mach,
        alpha_deg=alpha_deg,
    )

    import subprocess

    subprocess.run(
        ["vspaero", input_file],
        capture_output=True,
        text=True,
    )

    return parse_vspaero_output(output_file=output_file)


def generate_vspaero_sweep(
    *,
    geometry: AircraftGeometry,
    mach_range: list[float],
    alpha_range: list[float],
    output_prefix: str = "vspaero_sweep",
) -> dict:
    cl_grid: list[list[float]] = []
    cd_grid: list[list[float]] = []
    cm_grid: list[list[float]] = []
    l_d_grid: list[list[float]] = []

    for mach in mach_range:
        cl_row: list[float] = []
        cd_row: list[float] = []
        cm_row: list[float] = []
        l_d_row: list[float] = []

        for alpha in alpha_range:
            output_file = f"{output_prefix}_mach{mach:.2f}_alpha{alpha:.2f}.txt"
            input_file = f"{output_prefix}_mach{mach:.2f}_alpha{alpha:.2f}_input.txt"

            result = run_vspaero_analysis(
                geometry=geometry,
                mach=mach,
                alpha_deg=alpha,
                output_file=output_file,
                input_file=input_file,
            )

            cl_row.append(result.cl)
            cd_row.append(result.cd)
            cm_row.append(result.cm)
            l_d_row.append(result.cl / result.cd if result.cd > 0 else 0.0)

        cl_grid.append(cl_row)
        cd_grid.append(cd_row)
        cm_grid.append(cm_row)
        l_d_grid.append(l_d_row)

    return {
        "mach": mach_range,
        "alpha": alpha_range,
        "cl": cl_grid,
        "cd": cd_grid,
        "cm": cm_grid,
        "l_d": l_d_grid,
    }

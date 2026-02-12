from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .geometry_modeling import AircraftGeometry
    from ..common.atmosphere import isa_tropopause


@dataclass(frozen=True)
class AerodynamicLoad:
    lift: float
    drag: float
    moment_pitch: float
    moment_roll: float
    moment_yaw: float
    cl: float
    cd: float
    cm: float
    cn: float
    cy: float


@dataclass(frozen=True)
class InertialLoad:
    mass: float
    inertia: np.ndarray
    cg: np.ndarray
    acceleration: np.ndarray
    force: np.ndarray
    moment: np.ndarray


@dataclass(frozen=True)
class StructuralLoad:
    bending_moment: np.ndarray
    shear_force: np.ndarray
    torque: float
    von_mises_stress: float
    safety_factor: float


def calculate_aerodynamic_loads(
    *,
    geometry: AircraftGeometry,
    velocity: float,
    altitude_m: float,
    alpha_deg: float = 0.0,
    beta_deg: float = 0.0,
    sref: float | None = None,
) -> AerodynamicLoad:
    if velocity <= 0.0:
        raise ValueError("velocity must be positive.")
    if altitude_m < 0.0:
        raise ValueError("altitude_m must be non-negative.")

    atm = isa_tropopause(altitude_m, delta_t_k=0.0)
    rho = atm.rho_kg_m3
    if sref is None:
        sref = geometry.wing.area

    q = 0.5 * rho * velocity**2

    alpha_rad = alpha_deg * pi / 180.0
    cl = 2.0 * pi * alpha_rad
    cd = 0.02 + 0.05 * cl**2
    cm = -0.1 * cl

    lift = cl * q * sref
    drag = cd * q * sref
    moment_pitch = cm * q * sref * geometry.wing.chord_root

    moment_roll = 0.0
    moment_yaw = 0.0

    cn = cm / (geometry.wing.chord_root / geometry.wing.span)
    cy = 0.0

    return AerodynamicLoad(
        lift=lift,
        drag=drag,
        moment_pitch=moment_pitch,
        moment_roll=moment_roll,
        moment_yaw=moment_yaw,
        cl=cl,
        cd=cd,
        cm=cm,
        cn=cn,
        cy=cy,
    )


def calculate_inertial_loads(
    *,
    mass: float,
    cg: np.ndarray,
    acceleration: np.ndarray,
    inertia: np.ndarray | None = None,
) -> InertialLoad:
    if mass <= 0.0:
        raise ValueError("mass must be positive.")

    if inertia is None:
        inertia = np.eye(3) * mass

    force = mass * acceleration

    moment = np.cross(cg, force)

    return InertialLoad(
        mass=mass,
        inertia=inertia,
        cg=cg,
        acceleration=acceleration,
        force=force,
        moment=moment,
    )


def calculate_structural_loads(
    *,
    geometry: AircraftGeometry,
    aerodynamic_loads: AerodynamicLoad,
    inertial_loads: InertialLoad,
    material_yield_strength: float = 270.0e6,
    safety_factor: float = 1.5,
) -> StructuralLoad:
    span = geometry.wing.span
    num_stations = 20

    spanwise_locations = np.linspace(0, 1, num_stations)

    lift_distribution = np.zeros(num_stations)
    for i in range(num_stations):
        lift_distribution[i] = aerodynamic_loads.lift * (1.0 - abs(spanwise_locations[i] - 0.5))

    bending_moment = np.zeros(num_stations)
    for i in range(num_stations):
        moment = 0.0
        for j in range(i):
            moment += lift_distribution[j] * (spanwise_locations[i] - spanwise_locations[j]) * span
        bending_moment[i] = moment

    shear_force = np.zeros(num_stations)
    for i in range(num_stations):
        if i == 0:
            shear_force[i] = lift_distribution[i]
        else:
            shear_force[i] = shear_force[i - 1] - lift_distribution[i]

    torque = aerodynamic_loads.moment_pitch

    max_bending_moment = np.max(np.abs(bending_moment))
    max_shear_force = np.max(np.abs(shear_force))

    wing_chord = geometry.wing.chord_root
    thickness_ratio = float(getattr(geometry.wing, "thickness_to_chord_root", 0.12))
    section_modulus = (wing_chord**2) * (thickness_ratio**2) / 6.0

    bending_stress = max_bending_moment / section_modulus
    shear_stress = max_shear_force / (wing_chord * thickness_ratio)

    torsional_stress = torque / (section_modulus * 2.0)

    von_mises_stress = sqrt(bending_stress**2 + 3.0 * shear_stress**2 + torsional_stress**2)

    actual_safety_factor = material_yield_strength / von_mises_stress

    return StructuralLoad(
        bending_moment=bending_moment,
        shear_force=shear_force,
        torque=torque,
        von_mises_stress=von_mises_stress,
        safety_factor=actual_safety_factor,
    )


def calculate_load_envelope(
    *,
    geometry: AircraftGeometry,
    velocity_range: list[float],
    altitude_range: list[float],
    alpha_range: list[float],
    material_yield_strength: float = 270.0e6,
    safety_factor: float = 1.5,
) -> dict:
    lift_grid: list[list[float]] = []
    drag_grid: list[list[float]] = []
    moment_pitch_grid: list[list[float]] = []
    von_mises_grid: list[list[float]] = []
    safety_grid: list[list[float]] = []

    for velocity in velocity_range:
        lift_row: list[float] = []
        drag_row: list[float] = []
        moment_pitch_row: list[float] = []
        von_mises_row: list[float] = []
        safety_row: list[float] = []

        for altitude in altitude_range:
            for alpha in alpha_range:
                aero_loads = calculate_aerodynamic_loads(
                    geometry=geometry,
                    velocity=velocity,
                    altitude_m=altitude,
                    alpha_deg=alpha,
                )

                inertial_loads = calculate_inertial_loads(
                    mass=geometry.fuselage.length * 1000.0,
                    cg=geometry.fuselage.position,
                    acceleration=np.array([0.0, 0.0, 9.81]),
                )

                struct_loads = calculate_structural_loads(
                    geometry=geometry,
                    aerodynamic_loads=aero_loads,
                    inertial_loads=inertial_loads,
                    material_yield_strength=material_yield_strength,
                    safety_factor=safety_factor,
                )

                lift_row.append(aero_loads.lift)
                drag_row.append(aero_loads.drag)
                moment_pitch_row.append(aero_loads.moment_pitch)
                von_mises_row.append(struct_loads.von_mises_stress)
                safety_row.append(struct_loads.safety_factor)

        lift_grid.append(lift_row)
        drag_grid.append(drag_row)
        moment_pitch_grid.append(moment_pitch_row)
        von_mises_grid.append(von_mises_row)
        safety_grid.append(safety_row)

    return {
        "velocity": velocity_range,
        "altitude_m": altitude_range,
        "alpha": alpha_range,
        "lift": lift_grid,
        "drag": drag_grid,
        "moment_pitch": moment_pitch_grid,
        "von_mises_stress": von_mises_grid,
        "safety_factor": safety_grid,
    }


def calculate_flutter_analysis(
    *,
    geometry: AircraftGeometry,
    velocity: float,
    altitude_m: float,
) -> dict:
    atm = isa_tropopause(altitude_m, delta_t_k=0.0)
    rho = atm.rho_kg_m3
    sref = geometry.wing.area
    b = geometry.wing.span
    c_bar = sref / b

    mass = geometry.fuselage.length * 1000.0
    q = 0.5 * rho * velocity**2

    omega_flutter = sqrt((q * sref * c_bar) / (mass * (c_bar**2 / 4.0)))
    f_flutter = omega_flutter / (2.0 * pi)

    velocity_flutter = f_flutter * b

    return {
        "flutter_frequency_hz": f_flutter,
        "flutter_velocity_m_s": velocity_flutter,
        "flutter_angular_velocity_rad_s": omega_flutter,
    }

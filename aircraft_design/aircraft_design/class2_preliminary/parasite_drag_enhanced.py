from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

from ..common.atmosphere import isa_tropopause
from .degenerate_geometry import DegenPlate, DegenStick


@dataclass(frozen=True)
class ParasiteDragResult:
    cd0_total: float
    cd0_fric: float
    cd0_form: float
    cd0_interf: float
    reynolds_number: float
    cf_laminar: float
    cf_turbulent: float
    component_breakdown: dict


def calculate_reynolds_number(
    *,
    velocity: float,
    length: float,
    kinematic_viscosity: float = 1.4607e-5,
) -> float:
    if velocity <= 0.0:
        raise ValueError("velocity must be positive.")
    if length <= 0.0:
        raise ValueError("length must be positive.")
    if kinematic_viscosity <= 0.0:
        raise ValueError("kinematic_viscosity must be positive.")

    re = velocity * length / kinematic_viscosity
    return re


def calculate_friction_coefficient_laminar(
    *,
    reynolds_number: float,
) -> float:
    if reynolds_number <= 0.0:
        raise ValueError("reynolds_number must be positive.")

    cf = 1.328 / sqrt(reynolds_number)
    return cf


def calculate_friction_coefficient_turbulent(
    *,
    reynolds_number: float,
    roughness_ratio: float = 0.0,
) -> float:
    if reynolds_number <= 0.0:
        raise ValueError("reynolds_number must be positive.")
    if roughness_ratio < 0.0:
        raise ValueError("roughness_ratio must be >= 0.")

    if roughness_ratio == 0.0:
        if reynolds_number < 1.0e6:
            cf = 0.074 / (reynolds_number**0.2)
        else:
            cf = 0.074 / (reynolds_number**0.2)
    else:
        cf = 0.074 / (reynolds_number**0.2) + 0.045 * roughness_ratio

    return cf


def calculate_form_factor(
    *,
    thickness_ratio: float,
    sweep_angle_deg: float,
    mach: float = 0.0,
    fineness_ratio: float | None = None,
) -> float:
    if thickness_ratio <= 0.0 or thickness_ratio > 0.5:
        raise ValueError("thickness_ratio must be in (0, 0.5].")

    if fineness_ratio is not None:
        ff = 1.0 + 2.0 * thickness_ratio + 60.0 * (thickness_ratio**4)
    else:
        ff = 1.0 + 2.0 * thickness_ratio + 60.0 * (thickness_ratio**4)

    mach_correction = 1.0 + 0.2 * mach**2
    ff = ff * mach_correction

    return ff


def calculate_interference_factor(
    *,
    component_type: str,
    geometry: Any,
) -> float:
    if component_type == "wing":
        fi = 1.0
    elif component_type == "fuselage":
        fi = 1.05
    elif component_type == "horizontal_tail":
        fi = 1.1
    elif component_type == "vertical_tail":
        fi = 1.1
    elif component_type == "engine_nacelle":
        fi = 1.2
    elif component_type == "landing_gear":
        fi = 1.3
    else:
        raise ValueError(f"Unsupported component_type: {component_type}")

    return fi


def calculate_wetted_area(
    *,
    geometry: Any,
    sref: float,
) -> float:
    if isinstance(geometry, DegenPlate):
        swet = np.sum(geometry.area)
    elif isinstance(geometry, DegenStick):
        swet = 2.0 * np.sum(geometry.sect_area)
    else:
        swet = sref

    return swet


def calculate_parasite_drag_enhanced(
    *,
    geometry: Any,
    velocity: float,
    altitude_m: float,
    sref: float,
    surface_roughness: float = 0.0,
    isa_delta_c: float = 0.0,
) -> ParasiteDragResult:
    if velocity <= 0.0:
        raise ValueError("velocity must be positive.")
    if altitude_m < 0.0:
        raise ValueError("altitude_m must be non-negative.")
    if sref <= 0.0:
        raise ValueError("sref must be positive.")

    atm = isa_tropopause(altitude_m, delta_t_k=float(isa_delta_c))
    rho = atm.rho_kg_m3
    mu = atm.mu_kg_ms
    nu = mu / rho

    mach = velocity / atm.a_m_s

    swet = calculate_wetted_area(geometry=geometry, sref=sref)

    lref = sqrt(sref)

    re = calculate_reynolds_number(
        velocity=velocity,
        length=lref,
        kinematic_viscosity=nu,
    )

    cf_laminar = calculate_friction_coefficient_laminar(reynolds_number=re)

    cf_turbulent = calculate_friction_coefficient_turbulent(
        reynolds_number=re,
        roughness_ratio=surface_roughness / lref,
    )

    re_crit = 5.0e5
    if re < re_crit:
        cf = cf_laminar
    else:
        cf = cf_turbulent

    q = 0.5 * rho * velocity**2

    cd0_fric = cf * swet / sref

    if hasattr(geometry, "max_thickness"):
        thickness_ratio = geometry.max_thickness
    elif hasattr(geometry, "diameter"):
        thickness_ratio = geometry.diameter / lref
    else:
        thickness_ratio = 0.1

    if hasattr(geometry, "sweep_quarter_chord"):
        sweep_angle_deg = geometry.sweep_quarter_chord
    else:
        sweep_angle_deg = 0.0

    if hasattr(geometry, "fineness_ratio"):
        fineness_ratio = geometry.fineness_ratio
    else:
        fineness_ratio = None

    ff = calculate_form_factor(
        thickness_ratio=thickness_ratio,
        sweep_angle_deg=sweep_angle_deg,
        mach=mach,
        fineness_ratio=fineness_ratio,
    )

    cd0_form = ff * cd0_fric

    if isinstance(geometry, DegenPlate):
        component_type = "wing"
    elif isinstance(geometry, DegenStick):
        component_type = "wing"
    elif hasattr(geometry, "diameter"):
        component_type = "fuselage"
    else:
        component_type = "other"

    fi = calculate_interference_factor(
        component_type=component_type,
        geometry=geometry,
    )

    cd0_interf = fi * cd0_form

    cd0_total = cd0_fric + cd0_form + cd0_interf

    component_breakdown = {
        "cd0_fric": cd0_fric,
        "cd0_form": cd0_form,
        "cd0_interf": cd0_interf,
        "cf": cf,
        "ff": ff,
        "fi": fi,
        "swet": swet,
        "re": re,
        "mach": mach,
        "q": q,
    }

    return ParasiteDragResult(
        cd0_total=cd0_total,
        cd0_fric=cd0_fric,
        cd0_form=cd0_form,
        cd0_interf=cd0_interf,
        reynolds_number=re,
        cf_laminar=cf_laminar,
        cf_turbulent=cf_turbulent,
        component_breakdown=component_breakdown,
    )


def calculate_parasite_drag_sweep(
    *,
    geometry: Any,
    velocity_range: list[float],
    altitude_range: list[float],
    sref: float,
    surface_roughness: float = 0.0,
    isa_delta_c: float = 0.0,
) -> dict:
    cd0_total: list[list[float]] = []
    cd0_fric: list[list[float]] = []
    cd0_form: list[list[float]] = []
    cd0_interf: list[list[float]] = []
    reynolds_number: list[list[float]] = []
    cf: list[list[float]] = []
    ff: list[list[float]] = []
    fi: list[list[float]] = []
    swet: list[list[float]] = []
    mach: list[list[float]] = []

    for velocity in velocity_range:
        cd0_row: list[float] = []
        cd0_fric_row: list[float] = []
        cd0_form_row: list[float] = []
        cd0_interf_row: list[float] = []
        re_row: list[float] = []
        cf_row: list[float] = []
        ff_row: list[float] = []
        fi_row: list[float] = []
        swet_row: list[float] = []
        mach_row: list[float] = []

        for altitude in altitude_range:
            result = calculate_parasite_drag_enhanced(
                geometry=geometry,
                velocity=velocity,
                altitude_m=altitude,
                sref=sref,
                surface_roughness=surface_roughness,
                isa_delta_c=isa_delta_c,
            )

            cd0_row.append(result.cd0_total)
            cd0_fric_row.append(result.cd0_fric)
            cd0_form_row.append(result.cd0_form)
            cd0_interf_row.append(result.cd0_interf)
            re_row.append(result.reynolds_number)
            cf_row.append(result.component_breakdown["cf"])
            ff_row.append(result.component_breakdown["ff"])
            fi_row.append(result.component_breakdown["fi"])
            swet_row.append(result.component_breakdown["swet"])
            mach_row.append(result.component_breakdown["mach"])

        cd0_total.append(cd0_row)
        cd0_fric.append(cd0_fric_row)
        cd0_form.append(cd0_form_row)
        cd0_interf.append(cd0_interf_row)
        reynolds_number.append(re_row)
        cf.append(cf_row)
        ff.append(ff_row)
        fi.append(fi_row)
        swet.append(swet_row)
        mach.append(mach_row)

    return {
        "velocity": velocity_range,
        "altitude": altitude_range,
        "cd0_total": cd0_total,
        "cd0_fric": cd0_fric,
        "cd0_form": cd0_form,
        "cd0_interf": cd0_interf,
        "reynolds_number": reynolds_number,
        "cf": cf,
        "ff": ff,
        "fi": fi,
        "swet": swet,
        "mach": mach,
    }


def generate_parasite_drag_envelope(
    *,
    geometry: Any,
    sref: float,
    mach_range: list[float],
    altitude_range: list[float],
    surface_roughness: float = 0.0,
    isa_delta_c: float = 0.0,
) -> dict:
    cd0_total: list[list[float]] = []
    cd0_fric: list[list[float]] = []
    cd0_form: list[list[float]] = []
    cd0_interf: list[list[float]] = []
    reynolds_number: list[list[float]] = []
    cf: list[list[float]] = []
    ff: list[list[float]] = []
    fi: list[list[float]] = []
    swet: list[list[float]] = []

    for mach in mach_range:
        cd0_row: list[float] = []
        cd0_fric_row: list[float] = []
        cd0_form_row: list[float] = []
        cd0_interf_row: list[float] = []
        re_row: list[float] = []
        cf_row: list[float] = []
        ff_row: list[float] = []
        fi_row: list[float] = []
        swet_row: list[float] = []

        for altitude in altitude_range:
            atm = isa_tropopause(altitude, delta_t_k=float(isa_delta_c))
            velocity = mach * atm.a_m_s

            result = calculate_parasite_drag_enhanced(
                geometry=geometry,
                velocity=velocity,
                altitude_m=altitude,
                sref=sref,
                surface_roughness=surface_roughness,
                isa_delta_c=isa_delta_c,
            )

            cd0_row.append(result.cd0_total)
            cd0_fric_row.append(result.cd0_fric)
            cd0_form_row.append(result.cd0_form)
            cd0_interf_row.append(result.cd0_interf)
            re_row.append(result.reynolds_number)
            cf_row.append(result.component_breakdown["cf"])
            ff_row.append(result.component_breakdown["ff"])
            fi_row.append(result.component_breakdown["fi"])
            swet_row.append(result.component_breakdown["swet"])

        cd0_total.append(cd0_row)
        cd0_fric.append(cd0_fric_row)
        cd0_form.append(cd0_form_row)
        cd0_interf.append(cd0_interf_row)
        reynolds_number.append(re_row)
        cf.append(cf_row)
        ff.append(ff_row)
        fi.append(fi_row)
        swet.append(swet_row)

    return {
        "mach": mach_range,
        "altitude_m": altitude_range,
        "cd0_total": cd0_total,
        "cd0_fric": cd0_fric,
        "cd0_form": cd0_form,
        "cd0_interf": cd0_interf,
        "reynolds_number": reynolds_number,
        "cf": cf,
        "ff": ff,
        "fi": fi,
        "swet": swet,
    }

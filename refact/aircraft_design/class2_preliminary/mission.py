from __future__ import annotations

from dataclasses import dataclass

from ..common.atmosphere import isa_tropopause
from .constraints import AeroPolar
from .performance import required_thrust_newton
from .propulsion import PropulsionModel, fuel_flow_n_s
from ..common.units import CONST


@dataclass(frozen=True)
class SegmentResult:
    name: str
    fuel_fraction: float
    details: dict


def _fuel_fraction_from_weight_flow(
    *,
    w_initial_n: float,
    fuel_weight_flow_n_s: float,
    duration_s: float,
) -> float:
    if duration_s <= 0.0:
        return 0.0
    if w_initial_n <= 0.0:
        raise ValueError("w_initial_n must be positive.")
    wf_n = fuel_weight_flow_n_s * duration_s
    return min(0.95, max(0.0, wf_n / w_initial_n))


def mission_fuel_breakdown(
    *,
    w0_kg: float,
    s_m2: float,
    polar: AeroPolar,
    propulsion: PropulsionModel,
    mission: dict,
    isa_delta_c: float = 0.0,
) -> dict:
    w_n = w0_kg * CONST.g0_m_s2
    cruise_alt = float(mission["cruise_altitude_m"])
    cruise_v = float(mission["cruise_speed_m_s"])
    range_m = float(mission["range_m"])

    reserve_fraction = float(mission.get("reserve_fraction", 0.0))
    loiter_time_s = float(mission.get("loiter_time_s", 0.0))
    loiter_speed_m_s = float(mission.get("loiter_speed_m_s", cruise_v))
    alternate_range_m = float(mission.get("alternate_range_m", 0.0))

    segments: list[SegmentResult] = []

    taxi_fraction = float(mission.get("taxi_fraction", 0.01))
    w_start_n = w_n
    w_n *= 1.0 - taxi_fraction
    segments.append(
        SegmentResult(
            name="taxi_takeoff",
            fuel_fraction=taxi_fraction,
            details={
                "w_start_kg": w_start_n / CONST.g0_m_s2,
                "w_end_kg": w_n / CONST.g0_m_s2,
                "fuel_kg": (w_start_n - w_n) / CONST.g0_m_s2,
            },
        )
    )

    climb_v = float(mission.get("v_climb_m_s", 1.3 * float(mission["v_stall_m_s"])))
    climb_rate = float(mission.get("assumed_climb_rate_m_s", 3.0))
    # Climb Calculation
    # Average climb altitude approx 0.6 * cruise_alt for jet/turboprop to account for lapse
    avg_climb_alt = 0.6 * cruise_alt
    climb_atm = isa_tropopause(avg_climb_alt, delta_t_k=float(isa_delta_c))

    climb_time = max(0.0, cruise_alt / max(0.5, climb_rate))
    climb_dist = climb_time * climb_v

    # Calculate climb thrust at average altitude
    # Weight is approx w_n (start) - small burn. use w_n for conservative.
    d_climb = required_thrust_newton(
        rho_kg_m3=climb_atm.rho_kg_m3, v_m_s=climb_v, w_kg=w_n / CONST.g0_m_s2, s_m2=s_m2, polar=polar
    )
    # Add climb gradient thrust component?
    # T = D + W * sin(gamma). gamma = ROC / V.
    # required_thrust_newton only gives D.
    gamma_climb = climb_rate / max(1.0, climb_v)
    thrust_climb_total = d_climb + w_n * gamma_climb

    if propulsion.type == "jet":
        ff = fuel_flow_n_s(
            propulsion,
            thrust_n=thrust_climb_total,
            altitude_m=avg_climb_alt,
            speed_m_s=climb_v,
            isa_delta_c=isa_delta_c,
        )
        climb_fuel_fraction = _fuel_fraction_from_weight_flow(
            w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=climb_time
        )
        climb_details = {"time_s": climb_time, "thrust_required_n": thrust_climb_total, "distance_m": climb_dist}
    else:
        eta = propulsion.prop_efficiency if propulsion.prop_efficiency is not None else 0.8
        shaft_power = thrust_climb_total * climb_v / max(0.3, eta)
        ff = fuel_flow_n_s(propulsion, thrust_n=0.0, shaft_power_w=shaft_power)
        climb_fuel_fraction = _fuel_fraction_from_weight_flow(
            w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=climb_time
        )
        climb_details = {
            "time_s": climb_time,
            "shaft_power_w": shaft_power,
            "thrust_required_n": thrust_climb_total,
            "distance_m": climb_dist,
        }

    segments.append(SegmentResult(name="climb", fuel_fraction=climb_fuel_fraction, details=climb_details))
    w_start_n = w_n
    w_n *= 1.0 - climb_fuel_fraction
    climb_details.update(
        {
            "w_start_kg": w_start_n / CONST.g0_m_s2,
            "w_end_kg": w_n / CONST.g0_m_s2,
            "fuel_kg": (w_start_n - w_n) / CONST.g0_m_s2,
            "speed_m_s": climb_v,
        }
    )

    # Descent Estimation (to deduct range)
    # Descent usually at L/D max or idle glide.
    # Assume 3 degree glide slope.
    # Distance = Alt / tan(3 deg) ~ 19 * Alt
    descent_dist = 19.0 * cruise_alt

    # Cruise Calculation
    # Effective cruise range
    cruise_range = max(0.0, range_m - climb_dist - descent_dist)

    cruise_atm = isa_tropopause(cruise_alt, delta_t_k=float(isa_delta_c))
    d_cruise = required_thrust_newton(
        rho_kg_m3=cruise_atm.rho_kg_m3, v_m_s=cruise_v, w_kg=0.97 * (w_n / CONST.g0_m_s2), s_m2=s_m2, polar=polar
    )
    cruise_time = max(0.0, cruise_range / cruise_v)
    if propulsion.type == "jet":
        ff = fuel_flow_n_s(
            propulsion, thrust_n=d_cruise, altitude_m=cruise_alt, speed_m_s=cruise_v, isa_delta_c=isa_delta_c
        )
        cruise_fuel_fraction = _fuel_fraction_from_weight_flow(
            w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=cruise_time
        )
        cruise_details = {"time_s": cruise_time, "thrust_required_n": d_cruise, "distance_m": cruise_range}
    else:
        eta = propulsion.prop_efficiency if propulsion.prop_efficiency is not None else 0.8
        shaft_power = d_cruise * cruise_v / max(0.3, eta)
        ff = fuel_flow_n_s(propulsion, thrust_n=0.0, shaft_power_w=shaft_power)
        cruise_fuel_fraction = _fuel_fraction_from_weight_flow(
            w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=cruise_time
        )
        cruise_details = {
            "time_s": cruise_time,
            "shaft_power_w": shaft_power,
            "thrust_required_n": d_cruise,
            "distance_m": cruise_range,
        }

    segments.append(SegmentResult(name="cruise", fuel_fraction=cruise_fuel_fraction, details=cruise_details))
    w_start_n = w_n
    w_n *= 1.0 - cruise_fuel_fraction
    cruise_details.update(
        {
            "w_start_kg": w_start_n / CONST.g0_m_s2,
            "w_end_kg": w_n / CONST.g0_m_s2,
            "fuel_kg": (w_start_n - w_n) / CONST.g0_m_s2,
            "speed_m_s": cruise_v,
        }
    )

    if loiter_time_s > 0.0:
        loiter_atm = isa_tropopause(cruise_alt, delta_t_k=float(isa_delta_c))
        d_loiter = required_thrust_newton(
            rho_kg_m3=loiter_atm.rho_kg_m3,
            v_m_s=loiter_speed_m_s,
            w_kg=0.97 * (w_n / CONST.g0_m_s2),
            s_m2=s_m2,
            polar=polar,
        )
        if propulsion.type == "jet":
            ff = fuel_flow_n_s(
                propulsion,
                thrust_n=d_loiter,
                altitude_m=cruise_alt,
                speed_m_s=loiter_speed_m_s,
                isa_delta_c=isa_delta_c,
            )
            loiter_fuel_fraction = _fuel_fraction_from_weight_flow(
                w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=loiter_time_s
            )
            loiter_details = {"time_s": loiter_time_s, "thrust_required_n": d_loiter}
        else:
            eta = propulsion.prop_efficiency if propulsion.prop_efficiency is not None else 0.8
            shaft_power = d_loiter * loiter_speed_m_s / max(0.3, eta)
            ff = fuel_flow_n_s(propulsion, thrust_n=0.0, shaft_power_w=shaft_power)
            loiter_fuel_fraction = _fuel_fraction_from_weight_flow(
                w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=loiter_time_s
            )
            loiter_details = {"time_s": loiter_time_s, "shaft_power_w": shaft_power, "thrust_required_n": d_loiter}

        segments.append(SegmentResult(name="loiter", fuel_fraction=loiter_fuel_fraction, details=loiter_details))
        w_start_n = w_n
        w_n *= 1.0 - loiter_fuel_fraction
        loiter_details.update(
            {
                "w_start_kg": w_start_n / CONST.g0_m_s2,
                "w_end_kg": w_n / CONST.g0_m_s2,
                "fuel_kg": (w_start_n - w_n) / CONST.g0_m_s2,
                "speed_m_s": loiter_speed_m_s,
            }
        )

    if alternate_range_m > 0.0:
        alt_atm = isa_tropopause(cruise_alt, delta_t_k=float(isa_delta_c))
        d_alt = required_thrust_newton(
            rho_kg_m3=alt_atm.rho_kg_m3, v_m_s=cruise_v, w_kg=0.97 * (w_n / CONST.g0_m_s2), s_m2=s_m2, polar=polar
        )
        alt_time = max(0.0, alternate_range_m / cruise_v)
        if propulsion.type == "jet":
            ff = fuel_flow_n_s(propulsion, thrust_n=d_alt)
            alt_fuel_fraction = _fuel_fraction_from_weight_flow(
                w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=alt_time
            )
            alt_details = {"time_s": alt_time, "thrust_required_n": d_alt}
        else:
            eta = propulsion.prop_efficiency if propulsion.prop_efficiency is not None else 0.8
            shaft_power = d_alt * cruise_v / max(0.3, eta)
            ff = fuel_flow_n_s(propulsion, thrust_n=0.0, shaft_power_w=shaft_power)
            alt_fuel_fraction = _fuel_fraction_from_weight_flow(
                w_initial_n=w_n, fuel_weight_flow_n_s=ff, duration_s=alt_time
            )
            alt_details = {"time_s": alt_time, "shaft_power_w": shaft_power, "thrust_required_n": d_alt}

        segments.append(SegmentResult(name="alternate", fuel_fraction=alt_fuel_fraction, details=alt_details))
        w_start_n = w_n
        w_n *= 1.0 - alt_fuel_fraction
        alt_details.update(
            {
                "w_start_kg": w_start_n / CONST.g0_m_s2,
                "w_end_kg": w_n / CONST.g0_m_s2,
                "fuel_kg": (w_start_n - w_n) / CONST.g0_m_s2,
                "speed_m_s": cruise_v,
                "distance_m": alternate_range_m,
            }
        )

    descent_fraction = float(mission.get("descent_fraction", 0.01))
    w_start_n = w_n
    w_n *= 1.0 - descent_fraction
    segments.append(
        SegmentResult(
            name="descent",
            fuel_fraction=descent_fraction,
            details={
                "w_start_kg": w_start_n / CONST.g0_m_s2,
                "w_end_kg": w_n / CONST.g0_m_s2,
                "fuel_kg": (w_start_n - w_n) / CONST.g0_m_s2,
            },
        )
    )

    total_fraction = 0.0
    weight_multiplier = 1.0
    for s in segments:
        total_fraction = 1.0 - (1.0 - total_fraction) * (1.0 - s.fuel_fraction)
        weight_multiplier *= 1.0 - s.fuel_fraction

    total_fraction = 1.0 - (1.0 - total_fraction) * (1.0 - reserve_fraction)
    closure = 1.0 - weight_multiplier * (1.0 - reserve_fraction)

    return {
        "fuel_fraction_total": total_fraction,
        "reserve_fraction": reserve_fraction,
        "segments": [{"name": s.name, "fuel_fraction": s.fuel_fraction, "details": s.details} for s in segments],
        "closure": {"fuel_fraction_total_from_product": closure, "difference": total_fraction - closure},
    }


def generate_mission_envelope(
    *,
    w0_kg: float,
    s_m2: float,
    polar: AeroPolar,
    propulsion: PropulsionModel,
    cruise_altitude_m: float,
    cruise_speed_m_s: float,
    range_m: float,
    loiter_time_s: float = 0.0,
    loiter_speed_m_s: float | None = None,
    alternate_range_m: float = 0.0,
    reserve_fraction: float = 0.0,
    taxi_fraction: float = 0.01,
    descent_fraction: float = 0.01,
    isa_delta_c: float = 0.0,
) -> dict:
    base_mission = {
        "cruise_altitude_m": cruise_altitude_m,
        "cruise_speed_m_s": cruise_speed_m_s,
        "range_m": range_m,
        "loiter_time_s": loiter_time_s,
        "loiter_speed_m_s": loiter_speed_m_s if loiter_speed_m_s is not None else cruise_speed_m_s,
        "alternate_range_m": alternate_range_m,
        "reserve_fraction": reserve_fraction,
        "taxi_fraction": taxi_fraction,
        "descent_fraction": descent_fraction,
    }

    result = mission_fuel_breakdown(
        w0_kg=w0_kg,
        s_m2=s_m2,
        polar=polar,
        propulsion=propulsion,
        mission=base_mission,
        isa_delta_c=isa_delta_c,
    )

    total_fuel_fraction = result["fuel_fraction_total"]
    total_fuel_kg = w0_kg * total_fuel_fraction / (1.0 - reserve_fraction)

    return {
        "mission": base_mission,
        "fuel_breakdown": result,
        "total_fuel_kg": total_fuel_kg,
        "total_fuel_fraction": total_fuel_fraction,
        "reserve_fuel_kg": total_fuel_kg * reserve_fraction,
        "segments": result["segments"],
    }


def generate_range_envelope(
    *,
    w0_kg: float,
    s_m2: float,
    polar: AeroPolar,
    propulsion: PropulsionModel,
    cruise_altitude_m: float,
    cruise_speed_m_s: float,
    range_range: list[float],
    reserve_fraction: float = 0.0,
    taxi_fraction: float = 0.01,
    descent_fraction: float = 0.01,
    isa_delta_c: float = 0.0,
) -> dict:
    envelope = {
        "range_m": range_range,
        "total_fuel_kg": [],
        "reserve_fuel_kg": [],
        "fuel_fraction_total": [],
    }

    for range_m in range_range:
        result = generate_mission_envelope(
            w0_kg=w0_kg,
            s_m2=s_m2,
            polar=polar,
            propulsion=propulsion,
            cruise_altitude_m=cruise_altitude_m,
            cruise_speed_m_s=cruise_speed_m_s,
            range_m=range_m,
            reserve_fraction=reserve_fraction,
            taxi_fraction=taxi_fraction,
            descent_fraction=descent_fraction,
            isa_delta_c=isa_delta_c,
        )

        envelope["total_fuel_kg"].append(result["total_fuel_kg"])
        envelope["reserve_fuel_kg"].append(result["reserve_fuel_kg"])
        envelope["fuel_fraction_total"].append(result["fuel_fraction_total"])

    return envelope


def generate_payload_range_envelope(
    *,
    w_empty_kg: float,
    payload_range: list[float],
    s_m2: float,
    polar: AeroPolar,
    propulsion: PropulsionModel,
    cruise_altitude_m: float,
    cruise_speed_m_s: float,
    range_m: float,
    reserve_fraction: float = 0.0,
    taxi_fraction: float = 0.01,
    descent_fraction: float = 0.01,
    isa_delta_c: float = 0.0,
) -> dict:
    envelope = {
        "payload_kg": payload_range,
        "w0_kg": [],
        "total_fuel_kg": [],
        "mtow_kg": [],
    }

    for payload_kg in payload_range:
        w0_kg = w_empty_kg + payload_kg

        result = generate_mission_envelope(
            w0_kg=w0_kg,
            s_m2=s_m2,
            polar=polar,
            propulsion=propulsion,
            cruise_altitude_m=cruise_altitude_m,
            cruise_speed_m_s=cruise_speed_m_s,
            range_m=range_m,
            reserve_fraction=reserve_fraction,
            taxi_fraction=taxi_fraction,
            descent_fraction=descent_fraction,
            isa_delta_c=isa_delta_c,
        )

        envelope["w0_kg"].append(w0_kg)
        envelope["total_fuel_kg"].append(result["total_fuel_kg"])
        envelope["mtow_kg"].append(w0_kg + result["total_fuel_kg"])

    return envelope

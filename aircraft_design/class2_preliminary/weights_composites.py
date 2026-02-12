from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompositesCorrectionResult:
    weight_correction_factor: float
    details: dict


def calculate_composites_weight_correction(
    *,
    composite_fraction: float,
    weight_saving_fraction: float = 0.15,
) -> CompositesCorrectionResult:
    if composite_fraction <= 0.0 or composite_fraction > 1.0:
        raise ValueError("composite_fraction must be in (0, 1].")
    if weight_saving_fraction < 0.0 or weight_saving_fraction > 1.0:
        raise ValueError("weight_saving_fraction must be in [0, 1].")

    correction_factor = 1.0 - (composite_fraction * weight_saving_fraction)

    return CompositesCorrectionResult(
        weight_correction_factor=correction_factor,
        details={
            "composite_fraction": composite_fraction,
            "weight_saving_fraction": weight_saving_fraction,
            "correction_factor": correction_factor,
        },
    )


def calculate_composite_weight_adjustment(
    *,
    base_weight_kg: float,
    composite_fraction: float,
    weight_saving_fraction: float = 0.15,
) -> float:
    if base_weight_kg <= 0.0:
        raise ValueError("base_weight_kg must be positive.")

    correction = calculate_composites_weight_correction(
        composite_fraction=composite_fraction,
        weight_saving_fraction=weight_saving_fraction,
    )

    adjusted_weight_kg = base_weight_kg * correction.weight_correction_factor

    return adjusted_weight_kg


def calculate_composite_breakdown(
    *,
    base_weight_kg: float,
    composite_fraction: float,
    weight_saving_fraction: float = 0.15,
    component_breakdown: dict | None = None,
) -> dict:
    if base_weight_kg <= 0.0:
        raise ValueError("base_weight_kg must be positive.")

    correction_factor = 1.0 - (composite_fraction * weight_saving_fraction)

    if component_breakdown is None:
        component_breakdown = {
            "wing": 0.35,
            "fuselage": 0.30,
            "tail": 0.15,
            "landing_gear": 0.10,
            "other": 0.10,
        }

    adjusted_breakdown = {}
    total_adjusted = 0.0

    for component, fraction in component_breakdown.items():
        base_component_weight = base_weight_kg * fraction
        adjusted_component_weight = base_component_weight * correction_factor
        adjusted_breakdown[component] = adjusted_component_weight
        total_adjusted += adjusted_component_weight

    return {
        "correction_factor": correction_factor,
        "composite_fraction": composite_fraction,
        "weight_saving_fraction": weight_saving_fraction,
        "base_weight_kg": base_weight_kg,
        "adjusted_weight_kg": total_adjusted,
        "weight_saving_kg": base_weight_kg - total_adjusted,
        "component_breakdown": adjusted_breakdown,
    }


def generate_composites_sensitivity(
    *,
    base_weight_kg: float,
    composite_fraction_range: list[float] = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
    weight_saving_fraction: float = 0.15,
) -> dict:
    results = {
        "composite_fraction": composite_fraction_range,
        "correction_factor": [],
        "adjusted_weight_kg": [],
        "weight_saving_kg": [],
    }

    for cf in composite_fraction_range:
        correction = calculate_composites_weight_correction(
            composite_fraction=cf,
            weight_saving_fraction=weight_saving_fraction,
        )
        adjusted_weight = calculate_composite_weight_adjustment(
            base_weight_kg=base_weight_kg,
            composite_fraction=cf,
            weight_saving_fraction=weight_saving_fraction,
        )
        weight_saving = base_weight_kg - adjusted_weight

        results["correction_factor"].append(correction.weight_correction_factor)
        results["adjusted_weight_kg"].append(adjusted_weight)
        results["weight_saving_kg"].append(weight_saving)

    return results

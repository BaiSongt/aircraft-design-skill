from dataclasses import dataclass
from typing import List, Dict
from ..class3_detailed.geometry_detailed import DetailedFuselage, DetailedWing, estimate_wing_fuel_volume


@dataclass
class GeometricConstraint:
    name: str
    description: str
    passed: bool
    actual_value: float
    limit_value: float
    margin: float


class GeometryConstraintChecker:
    def __init__(self, wing: DetailedWing, fuselage: DetailedFuselage, requirements: Dict[str, float]):
        self.wing = wing
        self.fuselage = fuselage
        self.reqs = requirements
        self.results: List[GeometricConstraint] = []

    def check_all(self) -> List[GeometricConstraint]:
        self.check_fuel_volume()
        self.check_aspect_ratio()
        self.check_landing_gear_clearance()
        return self.results

    def check_fuel_volume(self):
        # Calculate available volume
        # Simple estimate: Wing volume * 0.7 (tank efficiency) * 0.85 (wet wing ratio)
        # Using imported estimator if available, else simple geometric
        # Assuming estimate_wing_fuel_volume returns m3
        vol_m3 = estimate_wing_fuel_volume(
            area_m2=self.wing.area,
            span_m=self.wing.span,
            t_c_root=self.wing.thickness_to_chord_root,
            t_c_tip=self.wing.thickness_to_chord_root,  # Simplified: assume constant t/c
            taper=self.wing.taper_ratio,
        )
        req_fuel_kg = self.reqs.get("fuel_weight_kg", 0.0)
        fuel_density = 800.0  # kg/m3 (Jet A)
        req_vol_m3 = req_fuel_kg / fuel_density

        passed = vol_m3 >= req_vol_m3
        self.results.append(
            GeometricConstraint(
                name="Fuel Volume",
                description="Available wing fuel volume vs Required fuel volume",
                passed=passed,
                actual_value=vol_m3,
                limit_value=req_vol_m3,
                margin=vol_m3 - req_vol_m3,
            )
        )

    def check_aspect_ratio(self):
        # Limit AR to avoid structural issues or gate limits (indirectly)
        # Example limit AR < 12 for standard cantilever
        limit = self.reqs.get("max_aspect_ratio", 14.0)
        ar = self.wing.span**2 / self.wing.area
        passed = ar <= limit
        self.results.append(
            GeometricConstraint(
                name="Aspect Ratio Limit",
                description=f"Aspect Ratio <= {limit}",
                passed=passed,
                actual_value=ar,
                limit_value=limit,
                margin=limit - ar,
            )
        )

    def check_landing_gear_clearance(self):
        # Example: Fuselage diameter vs upsweep for takeoff rotation
        # Simplified check
        pass

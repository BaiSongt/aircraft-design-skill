from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from math import sqrt, cos, radians


@dataclass
class SystemComponent:
    name: str
    weight_kg: float
    cg_x_m: float = 0.0
    cg_y_m: float = 0.0
    cg_z_m: float = 0.0
    power_w: float = 0.0
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "weight_kg": self.weight_kg,
            "cg_x_m": self.cg_x_m,
            "cg_y_m": self.cg_y_m,
            "cg_z_m": self.cg_z_m,
            "power_w": self.power_w,
            "cost_usd": self.cost_usd,
        }


@dataclass
class SystemGroup:
    name: str
    components: List[SystemComponent] = field(default_factory=list)

    @property
    def total_weight_kg(self) -> float:
        return sum(c.weight_kg for c in self.components)

    @property
    def total_power_w(self) -> float:
        return sum(c.power_w for c in self.components)

    @property
    def cg_x_m(self) -> float:
        w = self.total_weight_kg
        return sum(c.weight_kg * c.cg_x_m for c in self.components) / w if w > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "total_weight_kg": self.total_weight_kg,
            "cg_x_m": self.cg_x_m,
            "components": [c.to_dict() for c in self.components],
        }


@dataclass
class AircraftSystems:
    groups: Dict[str, SystemGroup] = field(default_factory=dict)

    def add_component(self, group_name: str, component: SystemComponent):
        if group_name not in self.groups:
            self.groups[group_name] = SystemGroup(name=group_name)
        self.groups[group_name].components.append(component)

    @property
    def total_weight_kg(self) -> float:
        return sum(g.total_weight_kg for g in self.groups.values())

    @property
    def total_power_w(self) -> float:
        return sum(g.total_power_w for g in self.groups.values())

    @property
    def empty_weight_kg(self) -> float:
        # Excludes payload, crew, fuel if they are in separate groups
        # Usually SystemsArchitecture defines Empty Weight components
        return self.total_weight_kg

    @property
    def cg_x_m(self) -> float:
        w_total = self.total_weight_kg
        if w_total <= 0:
            return 0.0
        moment = sum(g.total_weight_kg * g.cg_x_m for g in self.groups.values())
        return moment / w_total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_weight_kg": self.total_weight_kg,
            "total_power_w": self.total_power_w,
            "cg_x_m": self.cg_x_m,
            "groups": {k: v.to_dict() for k, v in self.groups.items()},
        }


def estimate_system_weights(
    mtow_kg: float,
    n_limit: float,
    geometry: Any,  # Can be ParametricGeometry or DetailedGeometry
    v_dive_m_s: float,
    tech_factor: float = 1.0,
    payload_kg: float = 0.0,
    crew_kg: float = 0.0,
    fuel_kg: float = 0.0,
    engine_dry_kg: Optional[float] = None,
    avionics_kg: Optional[float] = None,
    systems_config: Optional[Dict[str, Any]] = None,
    # Optional overrides if geometry object lacks these attributes (e.g. Class I geometry)
    s_ref_m2: Optional[float] = None,
    sh_m2: Optional[float] = None,
    sv_m2: Optional[float] = None,
) -> AircraftSystems:
    """
    Estimates component weights using semi-analytical methods (Raymer/Roskam adapted).
    Returns an AircraftSystems object populated with components.
    """
    sys = AircraftSystems()
    cfg = systems_config or {}

    # Helper to safely get geometry attributes regardless of class type
    def get_attr(obj, attrs, default=None):
        for a in attrs:
            if hasattr(obj, a):
                return getattr(obj, a)
        return default

    # 1. Wing Group
    # Raymer GA Approximation adapted
    # W_wing = 0.036 * S^0.758 * W_fw^0.0035 * (A / cos(L)^2)^0.6 * q^0.006 * tap^0.04 * (100 t/c)^-0.3 * (N W_dg)^0.49
    # Simplified for robustness:
    # W_wing ~ f(MTOW, N, S, AR, t/c)

    w_wing_kg = 0.0 * tech_factor  # Placeholder logic for now, will implement formula below

    # Raymer General Aviation / Homebuilt Wing Weight
    # W_wing = 0.0051 * (W_dg * N)^0.557 * S^0.649 * A^0.5 * (t/c)^-0.4 * (1+lambda)^0.1 * (cos(L))^-1.0 * S_csw^0.1
    # Note: W_dg is design gross weight (MTOW)

    wing_area = get_attr(geometry.wing, ["area"], s_ref_m2)
    if wing_area is None:
        raise ValueError("Wing area (s_ref_m2) must be provided either in geometry or as argument")

    S_ft2 = wing_area * 10.7639
    W_lbs = mtow_kg * 2.20462

    tc_root = get_attr(geometry.wing, ["thickness_to_chord_root", "t_c"], 0.12)
    AR = get_attr(geometry.wing, ["aspect_ratio"], 8.0)
    sweep_deg = get_attr(geometry.wing, ["sweep_qc", "sweep_quarter_chord_deg"], 0.0)
    sweep_rad = radians(sweep_deg)
    taper = get_attr(geometry.wing, ["taper_ratio"], 0.45)

    # Simplified Raymer GA formula
    w_wing_lbs = (
        0.0051
        * (W_lbs * n_limit) ** 0.557
        * S_ft2**0.649
        * AR**0.5
        * (tc_root) ** -0.4
        * (1 + taper) ** 0.1
        * (1.0 / cos(sweep_rad))
    )
    w_wing_kg = w_wing_lbs * 0.453592 * tech_factor

    # Wing CG: Approx 40% of MAC, roughly 40% of root chord back from LE
    # Better: Centroid of planform
    fus_len = get_attr(geometry.fuselage, ["length", "length_m"], 10.0)
    wing_mac = get_attr(geometry.wing, ["mean_aerodynamic_chord"], sqrt(wing_area / AR))  # Approx if missing

    wing_cg_x = fus_len * 0.4 + wing_mac * 0.4  # Rough placement

    sys.add_component("Structure", SystemComponent("Wing", w_wing_kg, cg_x_m=wing_cg_x))

    # 2. Fuselage Group
    # Raymer GA: W_fus = 0.035 * (W_dg * N)^0.377 * L^0.953 * (W_struct/W_dg)^-0.192? - Recursive
    # Alternative: W_fus = 0.052 * S_wet^1.086 * (W_dg * N)^0.177 * L^-0.051 * (L/D)^-0.072 * q^0.241
    # Let's use a wetted area based correlation

    if hasattr(geometry.fuselage, "wetted_area"):
        s_wet_fus_m2 = geometry.fuselage.wetted_area()
    else:
        # Cylinder approx
        fus_dia = get_attr(geometry.fuselage, ["diameter", "diameter_m"], 1.2)
        s_wet_fus_m2 = 3.14159 * fus_dia * fus_len * 0.9  # 0.9 for tapering

    S_wet_fus_ft2 = (s_wet_fus_m2 or 1.0) * 10.7639
    # Nicolai / Raymer hybrid for Fuselage
    # W_fus = 0.052 * S_wet^1.086 * (N*W)^0.177
    w_fus_lbs = 0.052 * (S_wet_fus_ft2**1.086) * ((n_limit * W_lbs) ** 0.177)
    w_fus_kg = w_fus_lbs * 0.453592 * tech_factor

    fus_cg_x = fus_len * 0.45  # Usually 40-50% of length

    sys.add_component("Structure", SystemComponent("Fuselage", w_fus_kg, cg_x_m=fus_cg_x))

    # 3. Empennage Group
    # Horizontal Tail
    ht_area_val = get_attr(geometry.tail, ["ht_area"], sh_m2)
    # Fallback if ht_area is missing but we have ratio (Class I geometry)
    if ht_area_val is None and hasattr(geometry.tail, "area_ratio_to_wing"):
        # Assume 80% of tail area is HT if only ratio is given?
        # Actually ParametricGeometry tail.area_ratio_to_wing is usually TOTAL or HT?
        # Let's assume it's mostly HT.
        ht_area_val = wing_area * geometry.tail.area_ratio_to_wing * 0.8  # Guess

    if ht_area_val and ht_area_val > 0:
        S_ht_ft2 = ht_area_val * 10.7639
        # W_ht = 0.016 * (N*W)^0.414 * q^0.168 * S_ht^0.896 * ...
        # Simplified: W_ht = 0.03 * (N*W)^0.4 * S_ht^0.7
        w_ht_lbs = 0.03 * ((n_limit * W_lbs) ** 0.4) * (S_ht_ft2**0.7)
        w_ht_kg = w_ht_lbs * 0.453592 * tech_factor

        ht_x = get_attr(geometry.tail, ["ht_x_le"], fus_len * 0.9)
        ht_cg_x = ht_x if ht_x else fus_len * 0.9
        sys.add_component("Structure", SystemComponent("Horizontal Tail", w_ht_kg, cg_x_m=ht_cg_x))

    # Vertical Tail
    vt_area_val = get_attr(geometry.tail, ["vt_area"], sv_m2)
    if vt_area_val is None and hasattr(geometry.tail, "area_ratio_to_wing"):
        # Guess VT is remaining 20%? Or usually VT is ~0.1-0.15 S_w.
        # Let's use 0.15 * S_w as fallback default if nothing else
        vt_area_val = wing_area * 0.15

    if vt_area_val and vt_area_val > 0:
        S_vt_ft2 = vt_area_val * 10.7639
        w_vt_lbs = 0.03 * ((n_limit * W_lbs) ** 0.4) * (S_vt_ft2**0.7)
        w_vt_kg = w_vt_lbs * 0.453592 * tech_factor

        vt_x = get_attr(geometry.tail, ["vt_x_le"], fus_len * 0.85)
        vt_cg_x = vt_x if vt_x else fus_len * 0.85
        sys.add_component("Structure", SystemComponent("Vertical Tail", w_vt_kg, cg_x_m=vt_cg_x))

    # 4. Landing Gear
    lg_cfg = cfg.get("landing_gear", {})
    lg_type = lg_cfg.get("type", "retractable")
    # Default fractions: Retractable ~5.7%, Fixed ~4.3%
    lg_frac_default = 0.057 if lg_type == "retractable" else 0.043
    lg_frac = float(lg_cfg.get("weight_fraction_override", lg_frac_default))

    w_lg_kg = lg_frac * mtow_kg
    if "weight_kg" in lg_cfg:
        w_lg_kg = float(lg_cfg["weight_kg"])

    lg_main_x = float(lg_cfg.get("main_gear_location_x_m", wing_cg_x))
    lg_nose_x = float(lg_cfg.get("nose_gear_location_x_m", fus_len * 0.1))

    sys.add_component("Systems", SystemComponent("Main Landing Gear", w_lg_kg * 0.85, cg_x_m=lg_main_x))
    sys.add_component("Systems", SystemComponent("Nose Landing Gear", w_lg_kg * 0.15, cg_x_m=lg_nose_x))

    # 5. Propulsion System
    # Engine weight (Dry) - usually input, but we can estimate if missing
    # W_eng_installed = 1.3 * W_eng_dry

    if engine_dry_kg is not None and engine_dry_kg > 0:
        # Installation factor 1.3 includes inlet, mounts, exhaust, cooling
        w_eng_total_kg = 1.3 * engine_dry_kg
    else:
        # Assume Engine is 15% of MTOW for generic sizing if unknown
        w_eng_total_kg = 0.15 * mtow_kg

    sys.add_component("Propulsion", SystemComponent("Engine Installed", w_eng_total_kg, cg_x_m=fus_len * 0.8))

    # Fuel System (Tanks, Pumps)
    # W_fs = 2.405 * V_fuel_gal^0.606 * ...
    # Simplified: 2% of MTOW
    sys.add_component("Propulsion", SystemComponent("Fuel System", 0.02 * mtow_kg, cg_x_m=wing_cg_x))

    # 6. Flight Controls
    fc_cfg = cfg.get("flight_controls", {})
    fc_tech = float(fc_cfg.get("tech_factor", 1.0))
    w_fc = 0.015 * mtow_kg * fc_tech
    if "weight_kg" in fc_cfg:
        w_fc = float(fc_cfg["weight_kg"])
    sys.add_component("Systems", SystemComponent("Flight Controls", w_fc, cg_x_m=fus_len * 0.5))

    # 7. Avionics
    av_cfg = cfg.get("avionics", {})
    w_av = avionics_kg if avionics_kg is not None else 0.03 * mtow_kg
    if "weight_kg" in av_cfg:
        w_av = float(av_cfg["weight_kg"])
    av_x = float(av_cfg.get("location_x_m", fus_len * 0.15))
    sys.add_component("Systems", SystemComponent("Avionics", w_av, cg_x_m=av_x))

    # 8. Furnishings & Equipment
    fur_cfg = cfg.get("furnishings", {})
    w_fur = 0.04 * mtow_kg
    if "weight_kg" in fur_cfg:
        w_fur = float(fur_cfg["weight_kg"])
    sys.add_component("Systems", SystemComponent("Furnishings", w_fur, cg_x_m=fus_len * 0.4))

    # 8.1 Environmental Control System (ECS)
    ecs_cfg = cfg.get("ecs", {})
    ecs_type = ecs_cfg.get("type", "basic")
    # Weight: approx 1-2% MTOW for small aircraft
    w_ecs = 0.015 * mtow_kg
    if "weight_kg" in ecs_cfg:
        w_ecs = float(ecs_cfg["weight_kg"])

    # Power estimate
    p_ecs = 500.0
    if ecs_type == "cycle":
        p_ecs = 3000.0

    sys.add_component("Systems", SystemComponent("ECS", w_ecs, cg_x_m=fus_len * 0.3, power_w=p_ecs))

    # 8.2 Anti-Ice System
    ai_cfg = cfg.get("anti_ice", {})
    ai_type = ai_cfg.get("type", "none")  # none, tks, boots, bleed, thermal_electric
    w_ai = 0.0
    p_ai = 0.0
    if ai_type != "none":
        # Base weight for system
        w_ai = 0.01 * mtow_kg
        if ai_type == "tks":
            w_ai += 20.0  # Fluid weight approx
            p_ai = 100.0  # Pumps
        elif ai_type == "thermal_electric":
            p_ai = 4000.0  # High power demand
        elif ai_type == "boots":
            p_ai = 200.0  # Pneumatic pumps

    if "weight_kg" in ai_cfg:
        w_ai = float(ai_cfg["weight_kg"])

    if w_ai > 0:
        sys.add_component("Systems", SystemComponent("Anti-Ice", w_ai, cg_x_m=wing_cg_x, power_w=p_ai))

    # 8.3 Electrical Group (Wiring, Batteries, Alternators)
    elec_cfg = cfg.get("electrical", {})
    # Weight: 2-3% MTOW
    w_elec = 0.025 * mtow_kg
    if "weight_kg" in elec_cfg:
        w_elec = float(elec_cfg["weight_kg"])

    sys.add_component("Systems", SystemComponent("Electrical", w_elec, cg_x_m=fus_len * 0.2))

    # Update Power for existing components
    # Avionics power
    sys_groups = sys.groups
    if "Systems" in sys_groups:
        for c in sys_groups["Systems"].components:
            if c.name == "Avionics":
                # Rough est: 15 W per kg of avionics?
                c.power_w = c.weight_kg * 15.0 if c.weight_kg > 0 else 500.0
            elif c.name == "Flight Controls":
                c.power_w = 200.0
            elif c.name == "Main Landing Gear":
                if lg_type == "retractable":
                    c.power_w = 0.0
            elif "Light" in c.name:
                c.power_w = 300.0

    if "Propulsion" in sys_groups:
        for c in sys_groups["Propulsion"].components:
            if "Fuel System" in c.name:
                c.power_w = 300.0  # Boost pumps

    # Extra Components from Config
    for key, val in cfg.items():
        if key not in ["landing_gear", "flight_controls", "avionics", "furnishings", "ecs", "anti_ice", "electrical"]:
            if isinstance(val, dict) and "weight_kg" in val:
                w = float(val["weight_kg"])
                x = float(val.get("location_x_m", fus_len * 0.5))
                # Auto-categorize? Default to Systems
                grp = "Systems"
                if "engine" in key or "prop" in key:
                    grp = "Propulsion"
                elif "wing" in key or "fuse" in key:
                    grp = "Structure"

                sys.add_component(grp, SystemComponent(key.replace("_", " ").title(), w, cg_x_m=x))

    # 9. Useful Load (Crew, Payload, Fuel)
    # These are not "Empty Weight" components but part of MTOW
    sys.add_component("Useful Load", SystemComponent("Crew", crew_kg, cg_x_m=fus_len * 0.15))
    sys.add_component("Useful Load", SystemComponent("Payload", payload_kg, cg_x_m=fus_len * 0.45))
    sys.add_component("Useful Load", SystemComponent("Fuel", fuel_kg, cg_x_m=wing_cg_x))

    return sys

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .design_loop_orchestrator import SizedAircraft


@dataclass
class Component:
    name: str
    weight_kg: float
    x_arm_m: float  # Distance from reference datum (usually nose)
    z_arm_m: float = 0.0  # Vertical distance (optional)

    @property
    def moment_kg_m(self) -> float:
        return self.weight_kg * self.x_arm_m


@dataclass
class LoadingScenario:
    name: str
    components: List[Component]
    total_weight_kg: float = field(init=False)
    cg_x_m: float = field(init=False)
    cg_z_m: float = field(init=False)

    def __post_init__(self):
        self.total_weight_kg = sum(c.weight_kg for c in self.components)
        total_moment_x = sum(c.moment_kg_m for c in self.components)
        total_moment_z = sum(c.weight_kg * c.z_arm_m for c in self.components)

        if self.total_weight_kg > 1e-6:
            self.cg_x_m = total_moment_x / self.total_weight_kg
            self.cg_z_m = total_moment_z / self.total_weight_kg
        else:
            self.cg_x_m = 0.0
            self.cg_z_m = 0.0


@dataclass
class CGEnvelope:
    forward_limit_m: float
    aft_limit_m: float
    forward_limit_mac_percent: float
    aft_limit_mac_percent: float
    mac_m: float
    mac_le_m: float
    scenarios: List[LoadingScenario]

    @property
    def points(self) -> List[Tuple[float, float]]:
        """
        Returns a list of (cg_x_m, weight_kg) points defining the envelope.
        """
        return [(s.cg_x_m, s.total_weight_kg) for s in self.scenarios]


class WeightBalanceAnalyzer:
    """
    Performs Center of Gravity (CG) analysis and envelope estimation.
    Fills the gap for Task 4 (Core Calculation Module).
    """

    def __init__(self, aircraft: SizedAircraft):
        self.ac = aircraft
        self.geo = aircraft.geometry
        self.wb = aircraft.weight_breakdown

        # Geometry extraction
        self.fuselage_len = self.geo.get("fuselage_length_m", 10.0)
        self.wing_span = self.geo.get("span_m", 10.0)
        self.wing_area = self.ac.wing_area_m2
        self.mac = self.geo.get("mean_chord_m", 1.5)
        self.root_chord = self.geo.get("root_chord_m", 2.0)

        # Assume Wing Leading Edge of MAC is at 35% of fuselage length (Configuration dependent)
        # This is a heuristic default for a generic layout.
        self.x_wing_le_mac = 0.35 * self.fuselage_len
        self.x_wing_apex = self.x_wing_le_mac  # Simplified, assuming LE is straight or this is the projected root LE

        # Estimate Component Arms (Heuristics)
        self._estimate_arms()

    def _estimate_arms(self):
        """
        Estimates the longitudinal position (arm) of major components.
        Reference Datum: Nose (X=0)
        """
        L = self.fuselage_len

        # 1. Structure
        # Wing: CG approx 40% MAC
        self.x_wing = self.x_wing_le_mac + 0.40 * self.mac

        # Fuselage: CG approx 45% Length
        self.x_fuselage = 0.45 * L

        # Tail (Empennage): Approx 95% Length (or derived from tail arm if known)
        # If we had tail arm in geometry, we'd use it.
        # Typically tail arm (ht) is 2.5-3.0 * MAC behind wing CG.
        self.x_tail = min(0.92 * L, self.x_wing + 3.0 * self.mac)

        # Landing Gear
        # Main: Behind Wing CG (approx 15 deg tipback angle), say 50% MAC
        self.x_gear_main = self.x_wing_le_mac + 0.55 * self.mac
        # Nose: Forward fuselage, say 10% Length
        self.x_gear_nose = 0.10 * L

        # 2. Propulsion
        # Engine: Depends on config.
        # Case A: Single Engine Jet (Fighter/Trainer) -> Aft
        # Case B: Prop (GA) -> Front
        # We'll infer from T/W or explicitly default to 'Aft' for this skill context (often fighter/jet examples)
        # Or check if 'num_engines' is in geometry.
        # Let's assume Aft Engine for generic jet context, or near wing for podded.
        # Defaulting to Aft Fuselage for now (common for the examples in memory).
        self.x_engine = 0.85 * L

        # 3. Systems
        self.x_systems = 0.40 * L  # Distributed, avg near nose/cockpit

        # 4. Payload & Crew
        # Crew: Cockpit, say 15% Length
        self.x_crew = 0.15 * L
        # Payload: Near CG to minimize trim change? Or nose (radar)?
        # Assume payload (ammo/bombs) near CG or slightly fwd.
        self.x_payload = self.x_wing_le_mac + 0.2 * self.mac

        # 5. Fuel
        # Wing Tank: Near Wing CG
        self.x_fuel = self.x_wing

    def generate_scenarios(self) -> List[LoadingScenario]:
        """
        Generates standard loading scenarios for envelope definition.
        """
        scenarios = []

        # Helper to get weight (safe get)
        def w(key, default=0.0):
            val = self.wb.get(key, default)
            # If breakdown has nested dicts (e.g. structure -> wing), handle that?
            # For now assume flat or handled by caller.
            # SizedAircraft has specific fields for major groups.
            return val

        # Weights from SizedAircraft
        w_pay = self.wb.get("payload", 0.0)  # Payload might be in breakdown
        if w_pay == 0:
            w_pay = self.ac.mtow_kg - self.ac.empty_weight_kg - self.ac.fuel_weight_kg

        w_fuel = self.ac.fuel_weight_kg
        w_empty = self.ac.empty_weight_kg

        # Breakdown of Empty Weight (Simplified if detailed breakdown missing)
        # If detailed breakdown exists in self.wb, use it. Else use ratios.
        w_struct = self.wb.get("structure", 0.5 * w_empty)
        w_sys = self.wb.get("systems", 0.5 * w_empty)
        # Further split structure if possible
        # Assume: Wing 35%, Fuselage 35%, Tail 15%, Gear 15% of Structure
        w_wing = 0.35 * w_struct
        w_fus = 0.35 * w_struct
        w_tail = 0.15 * w_struct
        w_gear = 0.15 * w_struct  # Split 10% Nose, 90% Main
        w_gear_n = 0.1 * w_gear
        w_gear_m = 0.9 * w_gear

        # Propulsion (Engine)
        # Often engine is in systems or separate.
        # Let's assume engine is part of 'Systems' or 'Propulsion' in breakdown.
        # Or estimate from Thrust.
        # If not explicit, assume 20% of Empty Weight is Engine (Systems reduced).
        w_eng = 0.20 * w_empty
        w_sys_rem = w_sys - w_eng if w_sys > w_eng else w_sys * 0.5

        # Base Components (Fixed for all scenarios)
        base_comps = [
            Component("Wing", w_wing, self.x_wing),
            Component("Fuselage", w_fus, self.x_fuselage),
            Component("Tail", w_tail, self.x_tail),
            Component("Nose Gear", w_gear_n, self.x_gear_nose),
            Component("Main Gear", w_gear_m, self.x_gear_main),
            Component("Engine", w_eng, self.x_engine),
            Component("Systems", w_sys_rem, self.x_systems),
            Component("Crew", 100.0, self.x_crew),  # 100kg Pilot
        ]

        # Scenario 1: OEW + Crew (Empty)
        scenarios.append(LoadingScenario("OEW + Crew", base_comps))

        # Scenario 2: MTOW (Full Fuel + Full Payload)
        full_comps = base_comps + [Component("Fuel", w_fuel, self.x_fuel), Component("Payload", w_pay, self.x_payload)]
        scenarios.append(LoadingScenario("MTOW", full_comps))

        # Scenario 3: ZFW (Max Payload, No Fuel)
        zfw_comps = base_comps + [Component("Payload", w_pay, self.x_payload)]
        scenarios.append(LoadingScenario("ZFW", zfw_comps))

        # Scenario 4: Ferry (Full Fuel, No Payload)
        ferry_comps = base_comps + [Component("Fuel", w_fuel, self.x_fuel)]
        scenarios.append(LoadingScenario("Ferry", ferry_comps))

        return scenarios

    def analyze(self) -> CGEnvelope:
        scenarios = self.generate_scenarios()

        cgs = [s.cg_x_m for s in scenarios]
        min_cg = min(cgs)
        max_cg = max(cgs)

        # Convert to % MAC
        # CG% = (CG - LE_MAC) / MAC
        min_pct = (min_cg - self.x_wing_le_mac) / self.mac * 100
        max_pct = (max_cg - self.x_wing_le_mac) / self.mac * 100

        return CGEnvelope(
            forward_limit_m=min_cg,
            aft_limit_m=max_cg,
            forward_limit_mac_percent=min_pct,
            aft_limit_mac_percent=max_pct,
            mac_m=self.mac,
            mac_le_m=self.x_wing_le_mac,
            scenarios=scenarios,
        )

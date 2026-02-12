from dataclasses import dataclass
from typing import Callable, List, Dict, Optional


@dataclass
class Variable:
    name: str
    description: str
    unit: str
    symbol: str


@dataclass
class Formula:
    id: str
    name: str
    description: str
    func: Callable
    conditions: str
    variables: List[Variable]
    source: str = "Standard Textbook"


class FormulaDatabase:
    def __init__(self):
        self.formulas: Dict[str, Formula] = {}

    def register(self, formula: Formula):
        self.formulas[formula.id] = formula

    def get_formula(self, id: str) -> Optional[Formula]:
        return self.formulas.get(id)

    def list_formulas(self) -> List[Formula]:
        return list(self.formulas.values())

    def generate_documentation(self) -> str:
        doc = "# Formula Database\n\n"
        for f in self.formulas.values():
            doc += f"## {f.id}: {f.name}\n"
            doc += f"- **Description**: {f.description}\n"
            doc += f"- **Conditions**: {f.conditions}\n"
            doc += f"- **Source**: {f.source}\n"
            doc += "### Variables\n"
            doc += "| Symbol | Name | Unit | Description |\n"
            doc += "|---|---|---|---|\n"
            for v in f.variables:
                doc += f"| {v.symbol} | {v.name} | {v.unit} | {v.description} |\n"
            doc += "\n"
        return doc


# Global Instance
DB = FormulaDatabase()


# Registration Helpers
def register_atmosphere():
    from .atmosphere import isa_tropopause

    DB.register(
        Formula(
            id="ATM-001",
            name="ISA Tropopause Model",
            description="Calculates temperature, pressure, density up to 11km.",
            func=isa_tropopause,
            conditions="h <= 11000m",
            variables=[
                Variable("h", "Altitude", "m", "Geopotential altitude"),
                Variable("T", "Temperature", "K", "Ambient temperature"),
                Variable("P", "Pressure", "Pa", "Ambient pressure"),
                Variable("rho", "Density", "kg/m3", "Air density"),
            ],
            source="ICAO Standard Atmosphere",
        )
    )


def register_breguet():
    from .weights_class1 import fuel_fraction_breguet_jet

    DB.register(
        Formula(
            id="PERF-001",
            name="Breguet Range Equation (Jet)",
            description="Calculates fuel fraction for jet aircraft cruise.",
            func=fuel_fraction_breguet_jet,
            conditions="Constant altitude/speed cruise, jet engine",
            variables=[
                Variable("R", "Range", "m", "Cruise range"),
                Variable("C", "SFC", "1/s", "Thrust specific fuel consumption"),
                Variable("V", "Velocity", "m/s", "True airspeed"),
                Variable("L/D", "Lift-to-Drag", "-", "Aerodynamic efficiency"),
                Variable("W_ratio", "Weight Ratio", "-", "W_final / W_initial"),
            ],
            source="Raymer Eq 3.6",
        )
    )


def register_lift_slope():
    from .aero_lift_slope import calculate_lift_slope_subsonic

    DB.register(
        Formula(
            id="AERO-001",
            name="Subsonic 3D Lift Slope",
            description="Calculates 3D wing lift slope from geometry.",
            func=calculate_lift_slope_subsonic,
            conditions="Subsonic, Linear region",
            variables=[
                Variable("AR", "Aspect Ratio", "-", "Wing aspect ratio"),
                Variable("M", "Mach", "-", "Mach number"),
                Variable("Lambda", "Sweep", "rad", "Quarter-chord sweep"),
                Variable("CLa", "Lift Slope", "1/rad", "3D Lift curve slope"),
            ],
            source="DATCOM / Raymer",
        )
    )


def register_climb():
    from .performance import climb_rate_m_s

    DB.register(
        Formula(
            id="PERF-002",
            name="Rate of Climb",
            description="Calculates steady state climb rate.",
            func=climb_rate_m_s,
            conditions="Steady climb, small angle approx if used",
            variables=[
                Variable("T", "Thrust", "N", "Available thrust"),
                Variable("D", "Drag", "N", "Aerodynamic drag"),
                Variable("V", "Velocity", "m/s", "True airspeed"),
                Variable("W", "Weight", "N", "Aircraft weight"),
                Variable("ROC", "Rate of Climb", "m/s", "Vertical speed"),
            ],
            source="Energy Method",
        )
    )


# Initialize
def init_db():
    register_atmosphere()
    register_breguet()
    register_lift_slope()
    register_climb()


init_db()

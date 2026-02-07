from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict, Callable, Any

from .atmosphere import isa_tropopause
from .weights_class1 import fuel_fraction_breguet_jet, EmptyWeightModel
from .aero_lift_slope import calculate_lift_slope_subsonic
from .performance import climb_rate_m_s
from .constraints import AeroPolar

@dataclass
class VerificationResult:
    case_name: str
    parameter: str
    expected: float
    actual: float
    error_percent: float
    passed: bool
    message: str = ""


class VerificationSuite:
    """
    Automated verification suite for aircraft design formulas.
    Addresses Task 2: Formula Verification and Expansion.
    """

    def __init__(self):
        self.results: List[VerificationResult] = []
        self.tolerance_percent = 0.1  # Target < 0.1% error

    def _check(self, case_name: str, param: str, expected: float, actual: float):
        if expected == 0:
            if actual == 0:
                error = 0.0
            else:
                error = 100.0 # Infinite error
        else:
            error = abs((actual - expected) / expected) * 100.0
            
        passed = error <= self.tolerance_percent
        
        self.results.append(VerificationResult(
            case_name=case_name,
            parameter=param,
            expected=expected,
            actual=actual,
            error_percent=error,
            passed=passed,
            message=f"Expected {expected:.4f}, got {actual:.4f}" if not passed else "OK"
        ))

    def run_all(self) -> str:
        """Runs all verification cases and returns a summary report."""
        self.results = []
        
        self._verify_atmosphere()
        self._verify_breguet_range()
        self._verify_lift_slope()
        self._verify_climb_performance()
        
        return self._generate_report()

    def _verify_atmosphere(self):
        # Case 1: Sea Level
        # Standard: T=288.15 K, P=101325 Pa, rho=1.225 kg/m3
        atm = isa_tropopause(0.0)
        self._check("Atmosphere SL", "Temperature (K)", 288.15, atm.t_k)
        self._check("Atmosphere SL", "Pressure (Pa)", 101325.0, atm.p_pa)
        self._check("Atmosphere SL", "Density (kg/m3)", 1.225, atm.rho_kg_m3)
        
        # Case 2: 11000m (Tropopause)
        # Standard: T=216.65 K, P=22632 Pa, rho=0.3648 kg/m3 (approx)
        # Exact calculation with R=287.05287 (from units.py):
        # T = 288.15 - 0.0065*11000 = 216.65
        # P = 101325 * (216.65/288.15)^(9.80665/(287.05287*0.0065)) = 22632.05
        # Rho = 22632.05 / (287.05287 * 216.65) = 0.36391
        atm_11k = isa_tropopause(11000.0)
        self._check("Atmosphere 11km", "Temperature (K)", 216.65, atm_11k.t_k)
        # Allow slight float diffs for pressure/density
        self._check("Atmosphere 11km", "Pressure (Pa)", 22632.1, atm_11k.p_pa) 
        self._check("Atmosphere 11km", "Density (kg/m3)", 0.3639, atm_11k.rho_kg_m3)

    def _verify_breguet_range(self):
        # Case: Jet Breguet
        # R = (V/c) * (L/D) * ln(Wi/Wf)
        # Invert to find fuel fraction: ff = 1 - 1 / exp(R*c / (V*L/D))
        # Inputs: R=1000km, V=200m/s, c=1e-4 1/s, L/D=10
        # Exponent = 1e6 * 1e-4 / (200 * 10) = 100 / 2000 = 0.05
        # exp(0.05) = 1.051271
        # ff = 1 - 1/1.051271 = 1 - 0.951229 = 0.04877
        
        ff = fuel_fraction_breguet_jet(
            range_m=1000e3,
            v_cruise_m_s=200.0,
            tsfc_1_s=1e-4,
            lift_to_drag=10.0
        )
        expected_ff = 1.0 - 1.0 / math.exp(1000e3 * 1e-4 / (200.0 * 10.0))
        self._check("Breguet Jet", "Fuel Fraction", expected_ff, ff)

    def _verify_lift_slope(self):
        # Case: DATCOM/Raymer approximation for subsonic unswept wing
        # CLa = 2*pi*A / (2 + sqrt(A^2 * (1 + tan^2(Lam)) * (1-M^2) + 4))
        # Simplify: M=0, Sweep=0 -> CLa = 2*pi*A / (2 + sqrt(A^2 + 4))
        # Let A=10
        # CLa = 2*pi*10 / (2 + sqrt(100+4)) = 62.83 / (2 + 10.198) = 62.83 / 12.198 = 5.15
        
        # Note: current lift_slope_transport implementation might be different (simple Helmbold or similar)
        # Let's check what it returns vs theoretical simple DATCOM
        ar = 10.0
        mach = 0.0
        sweep = 0.0
        
        result = calculate_lift_slope_subsonic(
            aspect_ratio=ar,
            mach=mach,
            sweep_quarter_chord_deg=sweep,
            sweep_max_thickness_deg=sweep # Assume same for unswept
        )
        
        # Theoretical Helmbold-Diederich for M=0, Sweep=0:
        # CLa = 2*pi*A / (2 + A) ? No, that's low aspect ratio approx.
        # Raymer Eq 12.6: 2*pi*A / (2 + sqrt(4 + A^2*(1-M^2)*(1+tan^2L)))
        # = 2*pi*10 / (2 + sqrt(4 + 100)) = 62.8318 / (2 + 10.198) = 5.1509
        
        self._check("Lift Slope (AR=10, M=0)", "CLa (/rad)", 5.1509, result.cl_alpha)

    def _verify_climb_performance(self):
        # Case: Simple Climb
        # Inputs:
        rho = 1.0
        v = 100.0
        w_kg = 1000.0
        s_m2 = 10.0
        thrust_n = 2000.0
        
        # Polar
        cd0 = 0.02
        e = 1.0
        ar = 10.0
        polar = AeroPolar(cd0=cd0, e=e, ar=ar)
        
        # Expected Calc
        # q = 0.5 * 1.0 * 100^2 = 5000
        # W_n = 1000 * 9.80665 = 9806.65
        # CL = 9806.65 / (5000 * 10) = 0.196133
        # K = 1 / (pi * 10) = 0.031831
        # CD = 0.02 + 0.031831 * 0.196133^2 = 0.021224
        # D = 5000 * 10 * 0.021224 = 1061.2
        # ROC = (2000 - 1061.2) * 100 / 9806.65 = 9.573
        
        roc = climb_rate_m_s(
            thrust_n=thrust_n,
            rho_kg_m3=rho,
            v_m_s=v,
            w_kg=w_kg,
            s_m2=s_m2,
            polar=polar
        )
        
        # Let's compute expected dynamically to avoid precision hardcoding issues
        from math import pi
        q = 0.5 * rho * v**2
        w_n = w_kg * 9.80665
        cl = w_n / (q * s_m2)
        k = 1.0 / (pi * e * ar)
        cd = cd0 + k * cl**2
        d = q * s_m2 * cd
        expected_roc = (thrust_n - d) * v / w_n
        
        self._check("Climb Rate", "ROC (m/s)", expected_roc, roc)

    def _generate_report(self) -> str:
        passed_count = sum(1 for r in self.results if r.passed)
        total_count = len(self.results)
        
        lines = [
            "# Formula Verification Report",
            f"**Total Cases**: {total_count}",
            f"**Passed**: {passed_count}",
            f"**Failed**: {total_count - passed_count}",
            f"**Pass Rate**: {passed_count/total_count*100:.1f}%",
            "",
            "## Detailed Results",
            "| Case | Parameter | Expected | Actual | Error (%) | Status |",
            "|:---|:---|:---|:---|:---|:---|"
        ]
        
        for r in self.results:
            status_icon = "✅" if r.passed else "❌"
            lines.append(f"| {r.case_name} | {r.parameter} | {r.expected:.4g} | {r.actual:.4g} | {r.error_percent:.3f}% | {status_icon} |")
            
        return "\n".join(lines)

if __name__ == "__main__":
    suite = VerificationSuite()
    print(suite.run_all())

from datetime import datetime
from typing import Dict, Any, List
import math
from .design_loop_orchestrator import SizedAircraft, DesignRequirements, InitialGuess

class DesignReportGenerator:
    """
    Generates professional aircraft design reports in Markdown format.
    """
    
    def __init__(self, project_name: str = "Untitled Project"):
        self.project_name = project_name
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def generate_markdown(self, aircraft: SizedAircraft, requirements: DesignRequirements, initial_guess: InitialGuess) -> str:
        """
        Generates the complete design report content.
        """
        sections = [
            self._header_section(),
            self._requirements_section(requirements),
            self._executive_summary(aircraft),
            self._geometry_section(aircraft),
            self._weight_engineering_section(aircraft),
            self._propulsion_section(aircraft),
            self._performance_section(aircraft, requirements),
            self._conclusion_section(aircraft)
        ]
        
        return "\n\n".join(sections)
    
    def _header_section(self) -> str:
        return f"""# Aircraft Conceptual Design Report
**Project Name**: {self.project_name}
**Date**: {self.timestamp}
**Status**: Preliminary Design Phase (Class I Sizing)

---
"""

    def _requirements_section(self, req: DesignRequirements) -> str:
        return f"""## 1. Mission Requirements
The aircraft is designed to meet the following mission specifications and performance constraints:

| Parameter | Value | Unit | Description |
| :--- | :--- | :--- | :--- |
| **Cruise Range** | {req.range_m / 1000:.1f} | km | Design Range |
| **Payload** | {req.payload_kg:.1f} | kg | Internal/External Payload |
| **Cruise Conditions** | Mach {req.cruise_mach:.2f} @ {req.cruise_altitude_m/1000:.1f} | km | Altitude & Speed |
| **Takeoff Distance** | {req.takeoff_distance_m:.0f} | m | Ground Roll + Air Distance |
| **Landing Distance** | {req.landing_distance_m:.0f} | m | Air Distance + Ground Roll |
| **Maneuverability** | {req.max_load_factor:.2f} | g | Max Load Factor (Limit) |
| **Sustained Turn** | {req.sustained_turn_g or 'N/A'} | g | Sustained Turn Capability |
| **Service Ceiling** | {req.service_ceiling_m or 'N/A'} | m | Service Ceiling |
"""

    def _executive_summary(self, ac: SizedAircraft) -> str:
        status_icon = "✅" if ac.converged else "❌"
        return f"""## 2. Executive Summary
The sizing process has **{'Converged' if ac.converged else 'Failed to Converge'}** {status_icon} after {ac.iterations} iterations.

### Key Design Parameters
*   **MTOW**: {ac.mtow_kg:.1f} kg
*   **Empty Weight**: {ac.empty_weight_kg:.1f} kg
*   **Fuel Weight**: {ac.fuel_weight_kg:.1f} kg
*   **Wing Area**: {ac.wing_area_m2:.2f} m²
*   **Thrust (SL Static)**: {ac.thrust_sl_n:.1f} N
*   **Thrust-to-Weight (T/W)**: {ac.thrust_sl_n / (ac.mtow_kg * 9.81):.3f}
*   **Wing Loading (W/S)**: {ac.mtow_kg * 9.81 / ac.wing_area_m2:.1f} Pa ({ac.mtow_kg / ac.wing_area_m2:.1f} kg/m²)
"""

    def _geometry_section(self, ac: SizedAircraft) -> str:
        geo = ac.geometry
        return f"""## 3. Configuration & Geometry
The baseline configuration is defined by the following geometric characteristics:

### Wing Geometry
*   **Area**: {ac.wing_area_m2:.2f} m²
*   **Span**: {geo.get('span_m', 0):.2f} m
*   **Aspect Ratio**: {geo.get('aspect_ratio', 0):.2f}
*   **Mean Chord**: {geo.get('mean_chord_m', 0):.2f} m
*   **Root Chord**: {geo.get('root_chord_m', 0):.2f} m
*   **Taper Ratio**: {geo.get('taper_ratio', 0):.2f}
*   **Sweep**: {geo.get('sweep_deg', 0):.1f}°

### Fuselage
*   **Length**: {geo.get('fuselage_length_m', 0):.2f} m
*   **Diameter (Equiv)**: {geo.get('fuselage_diameter_m', 0):.2f} m

### Empennage
*   **Horizontal Tail Area**: {geo.get('s_ht_m2', 0):.2f} m²
*   **Vertical Tail Area**: {geo.get('s_vt_m2', 0):.2f} m²
"""

    def _weight_engineering_section(self, ac: SizedAircraft) -> str:
        wb = ac.weight_breakdown
        # Create a table for weight breakdown
        table_rows = []
        for group, weight in wb.items():
            if isinstance(weight, dict):
                for sub, val in weight.items():
                     table_rows.append(f"| {group} - {sub} | {val:.1f} | {val/ac.mtow_kg*100:.1f}% |")
            else:
                table_rows.append(f"| {group} | {weight:.1f} | {weight/ac.mtow_kg*100:.1f}% |")
        
        table_content = "\n".join(table_rows)
        
        return f"""## 4. Weight Engineering
Detailed weight breakdown based on Class I statistical methods (Theory 03/Nicolai).

| Component | Weight (kg) | % MTOW |
| :--- | :--- | :--- |
{table_content}
| **MTOW** | **{ac.mtow_kg:.1f}** | **100%** |
"""

    def _propulsion_section(self, ac: SizedAircraft) -> str:
        return f"""## 5. Propulsion System
*   **Installed Thrust (SLS)**: {ac.thrust_sl_n:.1f} N
*   **Number of Engines**: 1 (Default assumption)
*   **Engine Dry Weight (Est)**: {ac.thrust_sl_n / (6.0 * 9.81):.1f} kg (based on T/W_eng ~ 6.0)
"""

    def _performance_section(self, ac: SizedAircraft, req: DesignRequirements) -> str:
        perf = {
            "Takeoff Distance": (ac.takeoff_distance_m, req.takeoff_distance_m),
            "Landing Distance": (ac.landing_distance_m, req.landing_distance_m),
            "Range": (ac.actual_range_m, req.range_m)
        }
        
        rows = []
        for name, (actual, required) in perf.items():
            margin = (required - actual) if "Distance" in name else (actual - required)
            margin_pct = (margin / required) * 100
            status = "PASS" if margin >= -0.01 else "FAIL" # -0.01 tolerance
            rows.append(f"| {name} | {required:.1f} | {actual:.1f} | {margin:+.1f} ({margin_pct:+.1f}%) | {status} |")
            
        return f"""## 6. Performance Compliance Matrix

| Metric | Requirement | Calculated | Margin | Status |
| :--- | :--- | :--- | :--- | :--- |
{chr(10).join(rows)}
"""

    def _conclusion_section(self, ac: SizedAircraft) -> str:
        return f"""## 7. Conclusion
The conceptual design phase has yielded a {'viable' if ac.converged else 'non-convergent'} configuration. 
{'The aircraft meets all primary performance constraints.' if ac.converged else 'Further iteration on the initial guess or relaxation of constraints is required.'}

***
*Generated by Aircraft Design Skill*
"""

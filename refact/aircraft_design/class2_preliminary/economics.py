from dataclasses import dataclass
from typing import Dict


@dataclass
class EconomicsResults:
    doc_total: float  # Total Direct Operating Cost per flight ($)
    doc_per_block_hour: float  # $ / hr
    doc_per_seat_mile: float  # $ / seat-mile
    breakdown: Dict[str, float]  # Breakdown of costs


class EconomicsAnalyzer:
    """
    Direct Operating Cost (DOC) Analysis based on standard industry models (e.g., AEA, NASA).
    """

    def calculate_doc(
        self,
        block_time_hr: float,
        flight_range_nm: float,
        fuel_burned_kg: float,
        aircraft_price_usd: float,
        engine_price_usd: float,  # Per engine
        num_engines: int,
        num_seats: int,
        mtow_kg: float,
        utilization_annual_hr: float = 3000.0,
        fuel_price_per_gal: float = 2.50,  # USD
        labor_rate_hr: float = 40.0,  # USD
        interest_rate: float = 0.05,
        insurance_rate: float = 0.005,
        depreciation_period_yr: float = 15.0,
        residual_value_fraction: float = 0.10,
    ) -> EconomicsResults:

        # 1. Fuel Cost
        # Density of Jet A ~ 0.8 kg/L = 6.7 lb/gal = 3.04 kg/gal
        # 1 kg = 0.329 gal
        fuel_gal = fuel_burned_kg * 0.329
        c_fuel = fuel_gal * fuel_price_per_gal

        # 2. Crew Cost (Simplified)
        # Pilot + Co-pilot. $200/hr combined?
        # Commercial standard: K * MTOW^0.4
        # Simple estimate: $150/hr for flight crew + cabin crew
        num_cabin_crew = max(1, int(num_seats / 50))
        c_crew = block_time_hr * (200.0 + num_cabin_crew * 50.0)

        # 3. Maintenance Cost
        # Airframe + Engine
        # C_maint = Labor + Materials
        # Simple parametric:
        # C_maint_hr = K * (Weight/1000)^0.5
        c_maint_hr = 15.0 * (mtow_kg / 1000.0) ** 0.5 * 2.0  # Factor for complexity
        c_maintenance = c_maint_hr * block_time_hr

        # 4. Depreciation
        # Cost per flight = (Price * (1 - Residual)) / (LifeYears * Utilization) * BlockTime
        depreciable_value = aircraft_price_usd * (1.0 - residual_value_fraction)
        c_depreciation = (depreciable_value / (depreciation_period_yr * utilization_annual_hr)) * block_time_hr

        # 5. Insurance
        c_insurance = (aircraft_price_usd * insurance_rate / utilization_annual_hr) * block_time_hr

        # 6. Interest
        # Average investment = Price * 0.6 (approx rule of thumb)
        avg_investment = aircraft_price_usd * 0.6
        c_interest = (avg_investment * interest_rate / utilization_annual_hr) * block_time_hr

        # 7. Fees (Landing, Navigation)
        # Landing fee ~ $5 per 1000kg MTOW
        c_landing = 5.0 * (mtow_kg / 1000.0)
        # Nav fee ~ Dist * Weight factor
        c_nav = 0.0  # Ignore for now
        c_fees = c_landing + c_nav

        # Total
        doc_total = c_fuel + c_crew + c_maintenance + c_depreciation + c_insurance + c_interest + c_fees

        return EconomicsResults(
            doc_total=doc_total,
            doc_per_block_hour=doc_total / block_time_hr if block_time_hr > 0 else 0,
            doc_per_seat_mile=doc_total / (num_seats * flight_range_nm) if (num_seats * flight_range_nm) > 0 else 0,
            breakdown={
                "Fuel": c_fuel,
                "Crew": c_crew,
                "Maintenance": c_maintenance,
                "Depreciation": c_depreciation,
                "Insurance": c_insurance,
                "Interest": c_interest,
                "Fees": c_fees,
            },
        )

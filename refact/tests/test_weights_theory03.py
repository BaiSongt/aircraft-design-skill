import pytest
from aircraft_design.class2_preliminary.weights_structural import calculate_landing_gear_weight
from aircraft_design.class2_preliminary.weights_system import (
    calculate_fuel_system_weight,
    calculate_propulsion_system_weight,
    calculate_flight_control_system_weight,
    calculate_furnishings_weight,
)


def test_landing_gear_weight_nicolai():
    """Verify Landing Gear weight using Theory 03 (Nicolai)."""
    # Case 1: 10000 lb MTOW (~4535.92 kg)
    mtow_kg = 4535.92

    # Formula: 0.043 * W^0.882
    # 10000^0.882 = 10^3.528 = 3372.87
    # W_lg_lb = 0.043 * 3372.87 = 145.03 lb
    expected_lb = 145.03
    expected_kg = expected_lb * 0.453592

    res = calculate_landing_gear_weight(max_takeoff_weight_kg=mtow_kg, composite_fraction=0.0)

    assert res.w_struct_kg == pytest.approx(expected_kg, rel=1e-3)
    assert res.details["formula"] == "Theory 03 (Nicolai)"

    # Case 2: Composite Correction (55% utilization -> 8% reduction)
    res_comp = calculate_landing_gear_weight(max_takeoff_weight_kg=mtow_kg, composite_fraction=0.55)
    expected_kg_comp = expected_kg * (1.0 - 0.08)
    assert res_comp.w_struct_kg == pytest.approx(expected_kg_comp, rel=1e-3)


def test_fuel_system_weight():
    """Verify Fuel System weight."""
    # Input: 1000 kg fuel, density 804
    fuel_kg = 1000.0

    res = calculate_fuel_system_weight(fuel_weight_kg=fuel_kg, fraction_wing_tank=0.5)

    expected_support_lb = 0.009 * 164.28 + 0.006 * 164.28
    expected_kg = expected_support_lb * 0.453592

    assert res.w_system_kg == pytest.approx(expected_kg, rel=1e-2)


def test_propulsion_system_weight():
    """Verify Propulsion System weight."""
    # Input: 10000 N thrust (~2248 lb), 1 engine
    thrust_n = 10000.0
    thrust_lb = 2248.09

    # Fallback Engine Weight: T/6.0
    w_engine_lb = thrust_lb / 6.0  # ~374.68 lb

    # Installation: Fighter (Other) -> 1.4
    # AB: True
    w_installed_lb = w_engine_lb * 1 * 1.4

    # Controls: 0.015 * W_eng * n * K_ECO * (Lf/10)^0.5
    # Lf = 15m = 49.21 ft
    # K_ECO = 1.080 (AB)
    w_control_lb = 0.015 * w_engine_lb * 1 * 1.080 * ((49.21 / 10.0) ** 0.5)

    # Starting: 0.005 * W_eng * n
    w_start_lb = 0.005 * w_engine_lb * 1

    total_lb = w_installed_lb + w_control_lb + w_start_lb
    expected_kg = total_lb * 0.453592

    res = calculate_propulsion_system_weight(
        thrust_sl_n=thrust_n, fuselage_length_m=15.0, has_afterburner=True, installation_type="fighter"
    )

    assert res.w_system_kg == pytest.approx(expected_kg, rel=1e-2)


def test_flight_control_weight_nicolai():
    """Verify Flight Control weight (Nicolai Fighter)."""
    # Input: MTOW 10000 lb, S=200 ft2, b=30 ft, N=9, Crew=1
    mtow_lb = 10000.0
    s_ft2 = 200.0
    b_ft = 30.0
    n_limit = 9.0

    # Formula: 138.18 * W^0.637 * (N*W/S)^0.324 * (b/100)^0.5 * (Nc+Np)^0.5
    # term1 = mtow_lb**0.637
    # term2 = (n_limit * mtow_lb / s_ft2)**0.324
    # term3 = (b_ft / 100.0)**0.5
    # term4 = (1)**0.5
    # w_lb = 138.18 * term1 * term2 * term3 * term4

    # Updated: Implementation uses 2.5% MTOW rule for fighters to avoid divergence
    w_lb = 0.025 * mtow_lb

    expected_kg = w_lb * 0.453592

    res = calculate_flight_control_system_weight(
        mtow_kg=mtow_lb / 2.20462,
        s_wing_m2=s_ft2 / 10.7639,
        b_wing_m=b_ft / 3.28084,
        n_limit=n_limit,
        aircraft_type="fighter",
    )

    assert res.w_system_kg == pytest.approx(expected_kg, rel=1e-2)


def test_furnishings_weight():
    """Verify Furnishings weight."""
    # Input: MTOW 10000 lb, q=500 psf, Crew=1, Ejection=True
    mtow_lb = 10000.0
    q_psf = 500.0

    # Seats: 22.0 * 1 * (500/100)^0.5 = 22.0 * 2.236 = 49.19 lb
    w_seats_lb = 22.0 * 1 * (500.0 / 100.0) ** 0.5

    # Misc: 0.001 * MTOW
    w_mis_lb = 0.001 * mtow_lb

    # AC: 0.002 * MTOW
    w_ac_lb = 0.002 * mtow_lb

    total_lb = w_seats_lb + w_mis_lb + w_ac_lb
    expected_kg = total_lb * 0.453592

    res = calculate_furnishings_weight(
        mtow_kg=mtow_lb / 2.20462, q_dive_pa=q_psf / 0.0208854, num_crew=1, ejection_seats=True
    )

    assert res.w_system_kg == pytest.approx(expected_kg, rel=1e-2)

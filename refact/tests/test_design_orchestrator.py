import pytest
from aircraft_design.class2_preliminary.design_loop_orchestrator import (
    DesignRequirements,
    InitialGuess,
    sizing_loop,
)
from aircraft_design.common.units import CONST


def test_sizing_loop_convergence():
    # 1. Requirements (Light Fighter)
    req = DesignRequirements(
        range_m=2000e3,
        payload_kg=1000.0,
        cruise_mach=0.8,
        cruise_altitude_m=11000.0,
        takeoff_distance_m=1000.0,
        landing_distance_m=1000.0,
        max_load_factor=7.33,
        sustained_turn_g=2.0,  # 2g sustained at 11km is realistic for light fighter
    )

    # 2. Initial Guess
    guess = InitialGuess(
        mtow_kg=12000.0,
        wing_loading_pa=3000.0,  # ~300 kg/m2
        thrust_to_weight=0.8,
        aspect_ratio=3.5,
        sweep_deg=35.0,
        taper_ratio=0.3,
        thickness_ratio=0.06,
        cd0=0.02,
        oswald_e=0.8,
        sfc_cruise_1_s=0.85 / 3600,  # ~2.36e-5
    )

    # 3. Run Loop
    result = sizing_loop(req, guess, max_iter=50)

    # 4. Assertions
    assert result.converged
    assert result.mtow_kg > 2000.0  # Sanity check (Light Fighter/Trainer)
    assert result.mtow_kg < 30000.0

    # Check Weight Breakdown validity
    wb = result.weight_breakdown
    assert "structure" in wb
    assert "systems" in wb
    assert "payload" in wb

    # Check if mass matches
    calc_mtow = wb["structure"] + wb["systems"] + wb["payload"] + result.fuel_weight_kg
    assert calc_mtow == pytest.approx(result.mtow_kg, rel=1e-3)

    # Check Geometry
    assert result.wing_area_m2 > 10.0
    assert result.thrust_sl_n > 20000.0


def test_sizing_loop_constraints_impact():
    """Test if stricter constraints force larger wing/engine."""
    req_strict = DesignRequirements(
        range_m=2000e3,
        payload_kg=1000.0,
        cruise_mach=0.8,
        cruise_altitude_m=11000.0,
        takeoff_distance_m=500.0,  # Very short takeoff -> High T/W
        landing_distance_m=1000.0,
        sustained_turn_g=2.0,  # Keep turn reasonable to isolate takeoff impact
    )

    guess = InitialGuess(
        mtow_kg=12000.0,
        wing_loading_pa=6000.0,  # Higher W/S to force higher T/W
        thrust_to_weight=0.5,  # Low guess
    )

    result = sizing_loop(req_strict, guess, max_iter=50)

    assert result.converged
    # Should have high T/W to meet 500m takeoff
    # T/W req approx > 1.0 for very short takeoff
    current_tw = result.thrust_sl_n / (result.mtow_kg * CONST.g0_m_s2)
    assert current_tw > 0.6  # Constraint forced T/W > 0.5 guess

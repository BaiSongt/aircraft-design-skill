import pytest
from aircraft_design.class2_preliminary.design_loop_orchestrator import sizing_loop
from aircraft_design.class2_preliminary.fixed_wing_overall import run_fixed_wing_overall_design


def test_sizing_loop_convergence(standard_requirements, standard_guess):
    """TC01: Verify sizing loop converges for standard inputs."""
    result = sizing_loop(standard_requirements, standard_guess)
    assert result.converged is True
    assert result.mtow_kg > 0
    assert result.fuel_weight_kg > 0
    assert result.wing_area_m2 > 0


def test_sizing_loop_divergence_handling(standard_requirements, standard_guess):
    """TC02: Verify handling of impossible requirements (should fail to converge or return high weight)."""
    # Request impossible range for a light fighter
    standard_requirements.range_m = 20000000.0  # 20,000 km

    # It might converge to a huge aircraft or hit max iterations
    result = sizing_loop(standard_requirements, standard_guess)

    # We expect it either not to converge OR result in a massive MTOW
    if result.converged:
        assert result.mtow_kg > 50000.0  # Should be very heavy
    else:
        assert result.converged is False


def test_input_validation_structure():
    """TC08: Verify input normalization logic handles missing fields via defaults."""
    minimal_input = {
        "mission": {
            "range_m": 1000e3,
            "cruise_altitude_m": 10000,
            "cruise_speed_m_s": 250,
            "v_stall_m_s": 50,
        },
        "payload": {"payload_kg": 500},
        "crew": {"crew_kg": 80},
        "aero": {"e": 0.8, "cl_max": 1.5},
        "sizing": {"wing_loading_pa": 3000, "aspect_ratio": 8, "thrust_to_weight": 0.4},
        "weights": {"empty_a": 0.9, "empty_b": -0.05},
        "propulsion": {"type": "prop"},
    }
    # This calls the underlying functional wrapper which normalizes inputs
    try:
        result = run_fixed_wing_overall_design(minimal_input)
        assert result is not None
        # Check if weights dict exists and contains w0_kg (MTOW)
        assert "weights" in result
        assert "w0_kg" in result["weights"]
    except Exception as e:
        pytest.fail(f"Minimal input raised exception: {e}")

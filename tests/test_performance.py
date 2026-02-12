import pytest
from aircraft_design.class2_preliminary.performance import calculate_sustained_turn_load, AeroPolar


def test_calculate_sustained_turn_load():
    # Setup
    polar = AeroPolar(cd0=0.02, e=0.8, ar=4.0)
    # K = 1 / (pi * 0.8 * 4.0) ~ 1/10 ~ 0.1
    # Let's calculate exact K
    # K = 1 / (3.14159 * 3.2) = 0.09947

    # Inputs
    thrust_n = 50000.0  # High thrust
    weight_kg = 10000.0
    s_m2 = 30.0
    rho_kg_m3 = 1.225
    v_m_s = 200.0  # ~Mach 0.6 at SL

    # Drag0 = q * S * CD0 = 24500 * 30 * 0.02 = 14700 N
    # Excess Thrust = 50000 - 14700 = 35300 N

    # n^2 = (Excess * q * S) / (K * W^2)
    # n^2 = (35300 * 24500 * 30) / (0.09947 * 98100^2)
    # n^2 = (2.59455e10) / (0.09947 * 9.6236e9)
    # n^2 = 2.59455e10 / 9.572e8 = 27.1
    # n = sqrt(27.1) ~ 5.2

    res = calculate_sustained_turn_load(
        thrust_n=thrust_n,
        weight_kg=weight_kg,
        s_m2=s_m2,
        polar=polar,
        rho_kg_m3=rho_kg_m3,
        v_m_s=v_m_s,
    )

    assert res["n_sustained"] == pytest.approx(5.2, abs=0.2)
    assert res["thrust_n"] == thrust_n
    assert res["n_thrust_limited"] == pytest.approx(5.2, abs=0.2)
    assert res["n_aero_limited"] is None
    assert res["n_struct_limited"] is None


def test_sustained_turn_load_limits():
    """Test with limits."""
    polar = AeroPolar(cd0=0.02, e=0.8, ar=4.0)

    # Inputs
    thrust_n = 50000.0  # High thrust -> n ~ 5.2
    weight_kg = 10000.0
    s_m2 = 30.0
    rho_kg_m3 = 1.225
    v_m_s = 200.0

    # Case 1: Aero limit (CL_max = 1.0)
    # n_aero = CL_max * q * S / W
    # q = 24500
    # W = 98100
    # n_aero = 1.0 * 24500 * 30 / 98100 = 7.49 (Not limiting if n_thrust is 5.2)

    # Let's use lower CL_max
    cl_max_low = 0.5
    # n_aero = 0.5 * 24500 * 30 / 98100 = 3.74

    res_aero = calculate_sustained_turn_load(
        thrust_n=thrust_n,
        weight_kg=weight_kg,
        s_m2=s_m2,
        polar=polar,
        rho_kg_m3=rho_kg_m3,
        v_m_s=v_m_s,
        cl_max=cl_max_low,
    )

    assert res_aero["n_sustained"] == pytest.approx(3.74, abs=0.1)
    assert res_aero["n_aero_limited"] == pytest.approx(3.74, abs=0.1)

    # Case 2: Structural limit
    n_struct_limit = 3.0
    res_struct = calculate_sustained_turn_load(
        thrust_n=thrust_n,
        weight_kg=weight_kg,
        s_m2=s_m2,
        polar=polar,
        rho_kg_m3=rho_kg_m3,
        v_m_s=v_m_s,
        max_load_factor=n_struct_limit,
    )

    assert res_struct["n_sustained"] == pytest.approx(3.0, abs=0.01)
    assert res_struct["n_struct_limited"] == 3.0

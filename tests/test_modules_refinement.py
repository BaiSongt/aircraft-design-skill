
import pytest
from aircraft_design.weights_structural import (
    calculate_wing_structural_weight,
    calculate_fuselage_structural_weight,
    calculate_horizontal_tail_structural_weight,
    calculate_vertical_tail_structural_weight,
    calculate_landing_gear_weight
)
from aircraft_design.propulsion import (
    build_propulsion_model,
    thrust_available_n,
    fuel_flow_n_s
)
from aircraft_design.units import CONST

def test_structural_weights_composite_correction():
    """Verify composite material weight reduction factors match Theory 03."""
    
    # Baseline (Metal)
    w_wing_metal = calculate_wing_structural_weight(
        s_wing_m2=20.0, aspect_ratio=5.0, sweep_quarter_chord_deg=30.0, taper_ratio=0.5,
        max_takeoff_weight_kg=10000.0, composite_fraction=0.0
    ).w_struct_kg
    
    w_fus_metal = calculate_fuselage_structural_weight(
        fuselage_length_m=15.0, fuselage_height_m=2.0, max_takeoff_weight_kg=10000.0,
        composite_fraction=0.0
    ).w_struct_kg
    
    w_lg_metal = calculate_landing_gear_weight(
        max_takeoff_weight_kg=10000.0, composite_fraction=0.0
    ).w_struct_kg

    # Composite (55% utilization)
    # Theory 03: Wing -25%, Fuselage -10%, LG -8%
    w_wing_comp = calculate_wing_structural_weight(
        s_wing_m2=20.0, aspect_ratio=5.0, sweep_quarter_chord_deg=30.0, taper_ratio=0.5,
        max_takeoff_weight_kg=10000.0, composite_fraction=0.55
    ).w_struct_kg
    
    w_fus_comp = calculate_fuselage_structural_weight(
        fuselage_length_m=15.0, fuselage_height_m=2.0, max_takeoff_weight_kg=10000.0,
        composite_fraction=0.55
    ).w_struct_kg
    
    w_lg_comp = calculate_landing_gear_weight(
        max_takeoff_weight_kg=10000.0, composite_fraction=0.55
    ).w_struct_kg
    
    # Check Ratios
    # Wing: 1 - 0.25 = 0.75
    assert w_wing_comp / w_wing_metal == pytest.approx(0.75, rel=1e-3)
    
    # Fuselage: 1 - 0.10 = 0.90
    assert w_fus_comp / w_fus_metal == pytest.approx(0.90, rel=1e-3)
    
    # LG: 1 - 0.08 = 0.92
    assert w_lg_comp / w_lg_metal == pytest.approx(0.92, rel=1e-3)
    
    # Partial Composite (e.g. 27.5% utilization -> half the reduction)
    w_wing_half = calculate_wing_structural_weight(
        s_wing_m2=20.0, aspect_ratio=5.0, sweep_quarter_chord_deg=30.0, taper_ratio=0.5,
        max_takeoff_weight_kg=10000.0, composite_fraction=0.275
    ).w_struct_kg
    
    # Wing: 1 - 0.125 = 0.875
    assert w_wing_half / w_wing_metal == pytest.approx(0.875, rel=1e-3)


def test_propulsion_mattingly_model():
    """Verify Mattingly low-bypass turbofan model behavior."""
    
    # Setup model
    prop_in = {
        "type": "jet",
        "thrust_sl_n": 50000.0,
        "tsfc_1_s": 0.8 / 3600.0, # 0.8 lb/lbf/hr approx
        "jet_model_method": "mattingly_low_bypass",
        "mct_to_mto_ratio": 0.85
    }
    model = build_propulsion_model(prop_in)
    
    # 1. Static Sea Level MTO
    # M=0, Alt=0 -> alpha approx 1.0 (Mattingly formula check: 1 - 0.3*0 + ... = 1)
    t_sl = thrust_available_n(model, altitude_m=0.0, speed_m_s=0.0, rating="mto")
    assert t_sl == pytest.approx(50000.0, rel=1e-2)
    
    # 2. High Speed Low Altitude (M=0.8, Alt=0)
    # alpha_ab = (1 - 0.3*0.8 + 0.2*0.64) * (1 / 1)^0.7
    # = (1 - 0.24 + 0.128) = 0.888
    t_m08 = thrust_available_n(model, altitude_m=0.0, speed_m_s=0.8 * 340.0, rating="mto")
    assert t_m08 / 50000.0 == pytest.approx(0.888, rel=0.05)
    
    # 3. High Altitude (Alt=11000m)
    # theta = T/T0 = 0.7519, delta = P/P0 = 0.2263
    # term2 = (delta / theta^0.8)^0.7 = (0.2263 / 0.7519^0.8)^0.7
    # 0.7519^0.8 ~= 0.796
    # 0.2263 / 0.796 ~= 0.284
    # 0.284^0.7 ~= 0.414


def test_propulsion_ab_sfc_logic():
    """Verify Afterburner SFC logic in fuel_flow_n_s."""
    
    # Setup model with AB parameters
    prop_in = {
        "type": "jet",
        "thrust_sl_n": 100000.0, # 100 kN
        "tsfc_1_s": 1.0e-4, # Base SFC
        "jet_model_method": "mattingly_low_bypass",
        "mct_to_mto_ratio": 0.6, # Mil is 60% of AB
        "mil_to_ab_sfc_ratio": 2.5 # AB SFC is 2.5x Base
    }
    model = build_propulsion_model(prop_in)
    
    # 1. Test in Mil Regime (Thrust < Mil Limit)
    # Mil Limit at SL = 100000 * 0.6 = 60000 N
    # Request 50000 N
    ff_mil = fuel_flow_n_s(model, thrust_n=50000.0, altitude_m=0.0, speed_m_s=0.0)
    
    # Expected SFC: Base * factor_mil * throttle_correction
    # M=0, Alt=0 -> factor_mil = 1.0
    # throttle = 50000 / 60000 = 0.8333...
    # throttle_corr = 1 + 0.2 * (1 - 0.8333...) = 1 + 0.2 * 0.1666... = 1.0333...
    
    throttle = 50000.0 / 60000.0
    expected_sfc_mil = 1.0e-4 * 1.0 * (1.0 + 0.2 * (1.0 - throttle))
    expected_ff_mil = expected_sfc_mil * 50000.0 * CONST.g0_m_s2
    
    assert ff_mil == pytest.approx(expected_ff_mil, rel=1e-3)
    
    # 2. Test in AB Regime (Thrust > Mil Limit)
    # Request 80000 N ( > 60000 N)
    ff_ab = fuel_flow_n_s(model, thrust_n=80000.0, altitude_m=0.0, speed_m_s=0.0)
    
    # Expected SFC: Base * factor_ab * ratio
    # M=0, Alt=0 -> factor_ab = 1.0
    # Ratio = 2.5
    
    expected_sfc_ab = 1.0e-4 * 1.0 * 2.5
    expected_ff_ab = expected_sfc_ab * 80000.0 * CONST.g0_m_s2
    
    assert ff_ab == pytest.approx(expected_ff_ab, rel=1e-3)

def test_propulsion_explicit_ab_sfc():
    """Verify that providing explicit tsfc_ab_1_s overrides the ratio."""
    
    # Setup model with explicit AB SFC
    # Mil SFC = 1.0e-4
    # AB SFC = 3.0e-4
    # Implied ratio = 3.0
    prop_in = {
        "type": "jet",
        "thrust_sl_n": 100000.0,
        "tsfc_1_s": 1.0e-4,
        "tsfc_ab_1_s": 3.0e-4, # Explicitly provided
        "jet_model_method": "mattingly_low_bypass",
        "mct_to_mto_ratio": 0.6,
        "mil_to_ab_sfc_ratio": 2.5 # Should be ignored/overridden
    }
    model = build_propulsion_model(prop_in)
    
    # Check if ratio was updated
    assert model.mil_to_ab_sfc_ratio == pytest.approx(3.0)
    
    # Test fuel flow in AB regime
    # Request 80000 N (> 60000 Mil limit)
    ff_ab = fuel_flow_n_s(model, thrust_n=80000.0, altitude_m=0.0, speed_m_s=0.0)
    
    # Expected: Base * factor_ab * ratio(3.0)
    expected_ff_ab = 1.0e-4 * 1.0 * 3.0 * 80000.0 * CONST.g0_m_s2
    
    assert ff_ab == pytest.approx(expected_ff_ab, rel=1e-3)

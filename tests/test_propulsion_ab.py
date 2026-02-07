import pytest
from aircraft_design.propulsion import build_propulsion_model, fuel_flow_n_s, thrust_available_n, PropulsionModel
from aircraft_design.units import CONST

def test_propulsion_ab_logic():
    """
    Verify that fuel flow increases significantly when thrust demand exceeds Mil thrust,
    indicating Afterburner usage.
    """
    # 1. Setup a Jet Model with AB capability
    prop_in = {
        "type": "jet",
        "thrust_sl_n": 50000.0,  # 50 kN SL Static (Max AB)
        "tsfc_1_s": 0.8 / 3600.0, # Mil SFC ~ 0.8 kg/kgf/hr
        "tsfc_ab_1_s": 2.0 / 3600.0, # AB SFC ~ 2.0 kg/kgf/hr
        "mil_to_ab_sfc_ratio": 2.5,
        "mct_to_mto_ratio": 0.6, # Mil is 60% of Max AB (Common for fighters: Mil~60kN, AB~100kN -> 0.6)
        "jet_model_method": "mattingly_low_bypass"
    }
    
    model = build_propulsion_model(prop_in)
    
    # Check Model Params
    print(f"Model Type: {model.type}")
    print(f"Thrust SL: {model.thrust_sl_n} N")
    print(f"Mil/AB Ratio: {model.mct_to_mto_ratio}")
    print(f"Mil SFC: {model.tsfc_1_s * 3600} 1/hr")
    
    # 2. Calculate Mil Thrust Available at a condition (e.g. SL, M0.5)
    alt = 0.0
    speed = 170.0 # ~M0.5
    
    t_mil = thrust_available_n(model, altitude_m=alt, speed_m_s=speed, rating="mct")
    t_max = thrust_available_n(model, altitude_m=alt, speed_m_s=speed, rating="mto")
    
    print(f"Mil Thrust Avail: {t_mil:.2f} N")
    print(f"Max Thrust Avail: {t_max:.2f} N")
    
    assert t_max > t_mil, "Max thrust should be greater than Mil thrust"
    
    # 3. Request Thrust just below Mil -> Should use Mil SFC
    req_mil = t_mil * 0.99
    ff_mil = fuel_flow_n_s(model, thrust_n=req_mil, altitude_m=alt, speed_m_s=speed)
    tsfc_eff_mil = ff_mil / (req_mil * CONST.g0_m_s2) * 3600.0
    print(f"Req: {req_mil:.2f} N -> FF: {ff_mil:.4f} kg/s -> TSFC: {tsfc_eff_mil:.4f}")
    
    # 4. Request Thrust above Mil -> Should use AB SFC
    req_ab = t_mil * 1.1
    ff_ab = fuel_flow_n_s(model, thrust_n=req_ab, altitude_m=alt, speed_m_s=speed)
    tsfc_eff_ab = ff_ab / (req_ab * CONST.g0_m_s2) * 3600.0
    print(f"Req: {req_ab:.2f} N -> FF: {ff_ab:.4f} kg/s -> TSFC: {tsfc_eff_ab:.4f}")
    
    # Expect TSFC jump
    ratio = tsfc_eff_ab / tsfc_eff_mil
    print(f"SFC Jump Ratio: {ratio:.2f}")
    
    assert ratio > 1.5, f"SFC should jump significantly in AB (got ratio {ratio:.2f})"
    assert tsfc_eff_ab > 1.5, "AB SFC should be high (>1.5)"
    
    # 5. Verify manual override logic if we wanted to FORCE AB at lower thrust?
    # Current implementation doesn't support forcing AB at low thrust via thrust_n alone 
    # unless thrust_n > t_mil. 
    # But user asked if they can "explicitly specify".
    # The current `fuel_flow_n_s` doesn't have an `afterburner=True` flag.
    # It infers from thrust level.
    # If we want to simulate "Max Power Takeoff", we just request T_max.
    
    # Check if we request exactly T_max
    ff_max = fuel_flow_n_s(model, thrust_n=t_max, altitude_m=alt, speed_m_s=speed)
    tsfc_eff_max = ff_max / (t_max * CONST.g0_m_s2) * 3600.0
    print(f"Req Max: {t_max:.2f} N -> TSFC: {tsfc_eff_max:.4f}")
    
    assert abs(tsfc_eff_max - tsfc_eff_ab) < 0.1, "Max thrust should have similar SFC to AB point"

if __name__ == "__main__":
    test_propulsion_ab_logic()

import pytest
from aircraft_design.design_loop_orchestrator import DesignRequirements, InitialGuess, SizedAircraft

@pytest.fixture
def standard_requirements():
    return DesignRequirements(
        range_m=2000000.0,
        payload_kg=1000.0,
        cruise_mach=0.8,
        cruise_altitude_m=11000.0,
        takeoff_distance_m=1000.0,
        landing_distance_m=1000.0,
        max_load_factor=7.33,
        sustained_turn_g=2.0,
        service_ceiling_m=15000.0
    )

@pytest.fixture
def standard_guess():
    return InitialGuess(
        mtow_kg=10000.0,
        thrust_to_weight=0.6,
        wing_loading_pa=3000.0,
        aspect_ratio=3.5,
        sweep_deg=45.0,
        taper_ratio=0.3,
        thickness_ratio=0.08,
        sfc_cruise_1_s=0.000222,
        cd0=0.02,
        oswald_e=0.8
    )

@pytest.fixture
def mock_sized_aircraft(standard_requirements, standard_guess):
    # Create a dummy SizedAircraft object for module testing
    # This avoids running the full loop for every unit test
    ac = SizedAircraft(
        converged=True,
        mtow_kg=5000.0,
        empty_weight_kg=3000.0,
        fuel_weight_kg=1000.0,
        wing_area_m2=20.0,
        thrust_sl_n=30000.0,
        geometry={
            "wing": {
                "span_m": 10.0,
                "area_m2": 20.0,
                "aspect_ratio": 5.0,
                "mean_chord_m": 2.0,
                "root_chord_m": 3.0,
                "tip_chord_m": 1.0,
                "sweep_deg": 30.0,
                "taper_ratio": 0.33,
                "thickness_to_chord_root": 0.12,
            },
            "fuselage": {
                "length_m": 12.0,
                "diameter_m": 1.5,
                "wetted_area_m2": 40.0
            },
            "tails": {
                "horizontal": {"area_m2": 4.0, "arm_m": 5.0},
                "vertical": {"area_m2": 3.0, "arm_m": 5.0}
            },
            "num_engines": 1
        },
        weight_breakdown={
            "structure": 1500.0,
            "propulsion": 800.0,
            "systems": 700.0,
            "payload": 1000.0,
            "crew": 100.0
        },
        actual_range_m=2100000.0,
        takeoff_distance_m=800.0,
        landing_distance_m=900.0,
        iterations=5
    )
    # Inject minimal objects needed for analyzers if they expect them attached
    # Note: Some analyzers might take the object itself or its components.
    # We'll adjust in tests if needed.
    return ac

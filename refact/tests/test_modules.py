from aircraft_design.class2_preliminary.stability_dynamic import DynamicStabilityAnalyzer
from aircraft_design.class2_preliminary.weight_balance import WeightBalanceAnalyzer
from aircraft_design.class2_preliminary.geometry_constraints import GeometryConstraintChecker
from aircraft_design.class3_detailed.geometry_detailed import DetailedWing, DetailedFuselage


def test_dynamic_stability_logic(mock_sized_aircraft):
    """TC04: Verify dynamic stability modes calculation."""
    analyzer = DynamicStabilityAnalyzer()

    # We need to construct inputs manually or infer from mock
    # The analyzer takes raw parameters, not SizedAircraft directly in some versions,
    # let's check the signature or use the report generator's integration logic.
    # Looking at report_generator_v2.py line 287, it calls analyze with many params.

    # We'll test the analyzer class directly with dummy data to ensure physics logic works
    res = analyzer.analyze(
        velocity_tas=200.0,
        density=0.5,
        wing_span=10.0,
        wing_chord=2.0,
        wing_area=20.0,
        mass=5000.0,
        ixx=10000.0,
        iyy=20000.0,
        izz=25000.0,
        cla=5.0,
        cma=-1.0,  # Stable
        cmq=-10.0,
        cnb=0.1,  # Stable directional
        clb=-0.1,  # Stable dihedral
        clp=-0.4,
        cnr=-0.15,
    )

    assert res.short_period_damping_ratio > 0
    assert res.phugoid_damping_ratio > 0
    assert res.dutch_roll_damping_ratio > 0
    assert res.spiral_time_constant != 0


def test_weight_balance_envelope(mock_sized_aircraft):
    """TC03: Verify CG envelope generation."""
    analyzer = WeightBalanceAnalyzer(mock_sized_aircraft)
    envelope = analyzer.analyze()

    assert envelope is not None
    assert len(envelope.points) > 0
    # Check if CGs are within some physical range (e.g., positive station)
    for p in envelope.points:
        # envelope.points returns list of (cg_x_m, weight_kg) tuples
        assert p[0] > 0
        assert p[1] > 0


def test_geometry_constraints():
    """TC05: Verify geometry constraints checking."""
    # Mock detailed geometry
    wing = DetailedWing(
        area=20.0,
        span=10.0,
        aspect_ratio=5.0,
        taper_ratio=0.5,
        sweep_qc=0.5,  # rad
        thickness_to_chord_root=0.12,
        dihedral=0.0,
        incidence=0.0,
        twist=0.0,
        x_le_root=5.0,
        y_root=0.0,
        z_root=0.0,
    )
    fuselage = DetailedFuselage(length=12.0, diameter=1.5, stations=[])

    reqs = {
        "fuel_weight_kg": 500.0,  # Small requirement
        "max_aspect_ratio": 10.0,
    }

    checker = GeometryConstraintChecker(wing, fuselage, reqs)
    results = checker.check_all()

    assert len(results) >= 2

    fuel_res = next(r for r in results if r.name == "Fuel Volume")
    ar_res = next(r for r in results if r.name == "Aspect Ratio Limit")

    assert fuel_res.passed is True
    assert ar_res.passed is True

    # Test failure case
    reqs_fail = {
        "fuel_weight_kg": 50000.0,  # Huge fuel req
        "max_aspect_ratio": 4.0,  # Strict AR limit (actual is 5.0)
    }
    checker_fail = GeometryConstraintChecker(wing, fuselage, reqs_fail)
    results_fail = checker_fail.check_all()

    fuel_res_fail = next(r for r in results_fail if r.name == "Fuel Volume")
    ar_res_fail = next(r for r in results_fail if r.name == "Aspect Ratio Limit")

    assert fuel_res_fail.passed is False
    assert ar_res_fail.passed is False

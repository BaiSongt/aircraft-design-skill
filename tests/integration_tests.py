from __future__ import annotations

import pytest
import numpy as np

from aircraft_design.airfoil_library import (
    AirfoilGeometry,
    generate_naca4_airfoil,
    generate_naca5_airfoil,
    generate_naca6_airfoil,
    load_airfoil_file,
    convert_airfoil_format,
    scale_airfoil,
    generate_airfoil_library,
)
from aircraft_design.geometry_modeling import (
    WingGeometry,
    FuselageGeometry,
    HorizontalTailGeometry,
    VerticalTailGeometry,
    EngineGeometry,
    LandingGearGeometry,
    AircraftGeometry,
    translate_geometry,
    rotate_geometry,
    scale_geometry,
    mirror_geometry,
    create_wing,
    create_fuselage,
    create_horizontal_tail,
    create_vertical_tail,
    create_engine,
    create_landing_gear,
    assemble_aircraft,
)
from aircraft_design.degenerate_geometry import (
    DegenPlate,
    DegenStick,
    DegenDisk,
    MassProperties,
    degenerate_wing_to_plate,
    degenerate_wing_to_stick,
    degenerate_fuselage_to_cylinder,
    degenerate_propeller_to_disk,
    calculate_mass_properties,
)
from aircraft_design.parasite_drag_enhanced import (
    ParasiteDragResult,
    calculate_parasite_drag_enhanced,
    calculate_parasite_drag_sweep,
    generate_parasite_drag_envelope,
)
from aircraft_design.surface_analysis import (
    SurfaceMesh,
    CurvatureResult,
    generate_surface_mesh,
    calculate_normals,
    calculate_curvature,
    calculate_surface_area,
    calculate_surface_centroid,
    calculate_surface_volume,
    generate_surface_mesh_from_geometry,
)
from aircraft_design.vspaero_interface import (
    VSPAEROResult,
    generate_vspaero_input,
    parse_vspaero_output,
    calculate_lift_distribution,
    calculate_drag_distribution,
    calculate_moment_coefficients,
    run_vspaero_analysis,
    generate_vspaero_sweep,
)
from aircraft_design.loads_analysis import (
    AerodynamicLoad,
    InertialLoad,
    StructuralLoad,
    calculate_aerodynamic_loads,
    calculate_inertial_loads,
    calculate_structural_loads,
    calculate_load_envelope,
    calculate_flutter_analysis,
)
from aircraft_design.rotorcraft_analysis import (
    RotorAerodynamics,
    RotorPerformance,
    calculate_rotor_aerodynamics,
    calculate_rotor_performance,
    calculate_rotor_performance_envelope,
    calculate_rotor_power_required,
    calculate_rotor_disk_loading,
    calculate_rotor_power_loading,
)


def test_airfoil_library():
    """测试翼型库模块"""
    naca4 = generate_naca4_airfoil(
        max_camber=0.02,
        max_camber_location=0.4,
        max_thickness=0.12,
    )
    assert isinstance(naca4, AirfoilGeometry)
    assert naca4.max_thickness > 0.0
    assert naca4.max_camber > 0.0

    naca5 = generate_naca5_airfoil(
        design_lift_coeff=0.3,
        max_thickness=0.12,
    )
    assert isinstance(naca5, AirfoilGeometry)
    assert naca5.max_thickness > 0.0

    naca6 = generate_naca6_airfoil(
        series_char="63",
        max_thickness=0.12,
        design_lift_coeff=0.3,
    )
    assert isinstance(naca6, AirfoilGeometry)
    assert naca6.max_thickness > 0.0

    library = generate_airfoil_library(
        naca4_params=[{"max_camber": 0.02, "max_camber_location": 0.4, "max_thickness": 0.12}],
        naca5_params=[{"design_lift_coeff": 0.3, "max_thickness": 0.12}],
        naca6_params=[{"series_char": "63", "max_thickness": 0.12, "design_lift_coeff": 0.3}],
    )
    assert len(library) == 3
    assert "NACA4_1" in library
    assert "NACA5_1" in library
    assert "NACA63_1" in library


def test_geometry_modeling():
    """测试几何建模模块"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )
    assert isinstance(wing, WingGeometry)
    assert wing.area == 30.0
    assert wing.span > 0.0

    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )
    assert isinstance(fuselage, FuselageGeometry)
    assert fuselage.length == 15.0
    assert fuselage.diameter == 2.0

    h_tail = create_horizontal_tail(
        area=8.0,
        aspect_ratio=5.0,
        taper_ratio=0.5,
        sweep_quarter_chord=30.0,
    )
    assert isinstance(h_tail, HorizontalTailGeometry)
    assert h_tail.area == 8.0

    v_tail = create_vertical_tail(
        area=5.0,
        aspect_ratio=2.0,
        taper_ratio=0.6,
        sweep_quarter_chord=35.0,
    )
    assert isinstance(v_tail, VerticalTailGeometry)
    assert v_tail.area == 5.0

    aircraft = assemble_aircraft(
        wing=wing,
        fuselage=fuselage,
        h_tail=h_tail,
        v_tail=v_tail,
    )
    assert isinstance(aircraft, AircraftGeometry)
    assert aircraft.wing == wing
    assert aircraft.fuselage == fuselage

    translated = translate_geometry(
        geometry=wing,
        dx=1.0,
        dy=0.0,
        dz=0.0,
    )
    assert translated.position[0] == 1.0

    rotated = rotate_geometry(
        geometry=wing,
        axis="z",
        angle_deg=10.0,
    )
    assert rotated.position[0] == wing.position[0]

    scaled = scale_geometry(
        geometry=wing,
        scale_factor=1.1,
    )
    assert scaled.area == wing.area * 1.1**2

    mirrored = mirror_geometry(
        geometry=wing,
        axis="y",
    )
    assert mirrored.position[1] == -wing.position[1]


def test_degenerate_geometry():
    """测试退化几何模块"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    plate = degenerate_wing_to_plate(
        wing=wing,
        num_chordwise=10,
        num_spanwise=5,
    )
    assert isinstance(plate, DegenPlate)
    assert plate.x.shape[0] == 10
    assert plate.x.shape[1] == 5

    stick = degenerate_wing_to_stick(
        wing=wing,
        num_sections=10,
    )
    assert isinstance(stick, DegenStick)
    assert len(stick.le) == 10

    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )

    cylinder = degenerate_fuselage_to_cylinder(
        fuselage=fuselage,
        num_sections=20,
    )
    assert isinstance(cylinder, DegenPlate)
    assert cylinder.x.shape[0] == 20

    disk = degenerate_propeller_to_disk(
        diameter=2.0,
        position=np.array([5.0, 0.0, 0.0]),
        normal=np.array([0.0, 0.0, 1.0]),
    )
    assert isinstance(disk, DegenDisk)
    assert disk.diameter == 2.0

    mass_props = calculate_mass_properties(
        geometry=plate,
        density=2700.0,
    )
    assert isinstance(mass_props, MassProperties)
    assert mass_props.area > 0.0
    assert mass_props.volume >= 0.0
    assert mass_props.mass > 0.0


def test_parasite_drag_enhanced():
    """测试增强寄生阻力模块"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    result = calculate_parasite_drag_enhanced(
        geometry=wing,
        velocity=200.0,
        altitude_m=10000.0,
        sref=30.0,
    )
    assert isinstance(result, ParasiteDragResult)
    assert result.cd0_total > 0.0
    assert result.reynolds_number > 0.0
    assert result.cd0_fric > 0.0
    assert result.cd0_form > 0.0

    sweep_result = calculate_parasite_drag_sweep(
        geometry=wing,
        velocity_range=[100.0, 150.0, 200.0],
        altitude_range=[0.0, 5000.0, 10000.0],
        sref=30.0,
    )
    assert len(sweep_result["velocity"]) == 3
    assert len(sweep_result["altitude"]) == 3
    assert len(sweep_result["cd0_total"]) == 3

    envelope = generate_parasite_drag_envelope(
        geometry=wing,
        sref=30.0,
        mach_range=[0.3, 0.5, 0.7],
        altitude_range=[0.0, 5000.0, 10000.0],
    )
    assert len(envelope["mach"]) == 3
    assert len(envelope["altitude_m"]) == 3
    assert len(envelope["cd0_total"]) == 3


def test_surface_analysis():
    """测试表面分析模块"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    plate = degenerate_wing_to_plate(
        wing=wing,
        num_chordwise=10,
        num_spanwise=5,
    )

    mesh = generate_surface_mesh(
        geometry=plate,
        num_u=10,
        num_v=5,
    )
    assert isinstance(mesh, SurfaceMesh)
    assert mesh.x.shape[0] == 10
    assert mesh.x.shape[1] == 5

    normals = calculate_normals(mesh=mesh)
    assert isinstance(normals, SurfaceMesh)
    assert normals.x.shape == mesh.x.shape

    curvature = calculate_curvature(mesh=mesh)
    assert isinstance(curvature, CurvatureResult)
    assert curvature.principal_curvature_1.shape == mesh.x.shape
    assert curvature.gaussian_curvature.shape == mesh.x.shape

    area = calculate_surface_area(mesh=mesh)
    assert area > 0.0

    centroid = calculate_surface_centroid(mesh=mesh)
    assert len(centroid) == 3

    volume = calculate_surface_volume(mesh=mesh)
    assert volume >= 0.0


def test_vspaero_interface():
    """测试VSPAERO接口模块"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )

    h_tail = create_horizontal_tail(
        area=8.0,
        aspect_ratio=5.0,
        taper_ratio=0.5,
        sweep_quarter_chord=30.0,
    )

    v_tail = create_vertical_tail(
        area=5.0,
        aspect_ratio=2.0,
        taper_ratio=0.6,
        sweep_quarter_chord=35.0,
    )

    aircraft = assemble_aircraft(
        wing=wing,
        fuselage=fuselage,
        h_tail=h_tail,
        v_tail=v_tail,
    )

    input_file = "test_vspaero_input.txt"
    output_file = "test_vspaero_output.txt"

    generate_vspaero_input(
        geometry=aircraft,
        output_file=input_file,
        mach=0.7,
        alpha_deg=0.0,
    )

    result = VSPAEROResult(
        cl=0.5,
        cd=0.03,
        cm=-0.1,
        cn=0.0,
        cy=0.0,
        cl_alpha=5.5,
        cd_alpha=0.2,
        lift_distribution={},
        drag_distribution={},
        moment_coefficients={},
    )

    lift_dist = calculate_lift_distribution(
        vspaero_results=result,
        geometry=aircraft,
    )
    assert "spanwise_location" in lift_dist
    assert "lift_coefficient" in lift_dist

    drag_dist = calculate_drag_distribution(
        vspaero_results=result,
        geometry=aircraft,
    )
    assert "spanwise_location" in drag_dist
    assert "drag_coefficient" in drag_dist

    moments = calculate_moment_coefficients(vspaero_results=result)
    assert "pitch_moment" in moments
    assert "roll_moment" in moments
    assert "yaw_moment" in moments

    sweep = generate_vspaero_sweep(
        geometry=aircraft,
        mach_range=[0.5, 0.7],
        alpha_range=[0.0, 5.0],
        output_prefix="test_sweep",
    )
    assert len(sweep["mach"]) == 2
    assert len(sweep["alpha"]) == 2
    assert len(sweep["cl"]) == 2


def test_loads_analysis():
    """测试载荷分析模块"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )

    aircraft = assemble_aircraft(
        wing=wing,
        fuselage=fuselage,
        h_tail=create_horizontal_tail(
            area=8.0,
            aspect_ratio=5.0,
            taper_ratio=0.5,
            sweep_quarter_chord=30.0,
        ),
        v_tail=create_vertical_tail(
            area=5.0,
            aspect_ratio=2.0,
            taper_ratio=0.6,
            sweep_quarter_chord=35.0,
        ),
    )

    aero_loads = calculate_aerodynamic_loads(
        geometry=aircraft,
        velocity=200.0,
        altitude_m=10000.0,
        alpha_deg=0.0,
    )
    assert isinstance(aero_loads, AerodynamicLoad)
    assert aero_loads.lift > 0.0
    assert aero_loads.drag > 0.0

    inertial_loads = calculate_inertial_loads(
        mass=10000.0,
        cg=np.array([0.0, 0.0, 0.0]),
        acceleration=np.array([0.0, 0.0, 9.81]),
    )
    assert isinstance(inertial_loads, InertialLoad)
    assert inertial_loads.mass == 10000.0
    assert len(inertial_loads.force) == 3

    struct_loads = calculate_structural_loads(
        geometry=aircraft,
        aerodynamic_loads=aero_loads,
        inertial_loads=inertial_loads,
        material_yield_strength=270.0e6,
        safety_factor=1.5,
    )
    assert isinstance(struct_loads, StructuralLoad)
    assert len(struct_loads.bending_moment) == 20
    assert len(struct_loads.shear_force) == 20
    assert struct_loads.safety_factor > 1.0

    envelope = calculate_load_envelope(
        geometry=aircraft,
        velocity_range=[100.0, 150.0, 200.0],
        altitude_range=[0.0, 5000.0, 10000.0],
        alpha_range=[0.0, 5.0],
        material_yield_strength=270.0e6,
        safety_factor=1.5,
    )
    assert len(envelope["velocity"]) == 3
    assert len(envelope["altitude_m"]) == 3
    assert len(envelope["alpha"]) == 3

    flutter = calculate_flutter_analysis(
        geometry=aircraft,
        velocity=200.0,
        altitude_m=10000.0,
    )
    assert "flutter_frequency_hz" in flutter
    assert "flutter_velocity_m_s" in flutter


def test_rotorcraft_analysis():
    """测试旋翼机分析模块"""
    rotor_aero = calculate_rotor_aerodynamics(
        rotor_diameter=10.0,
        rotor_speed_rpm=300.0,
        blade_pitch_deg=10.0,
        num_blades=4,
        air_density=1.225,
        altitude_m=0.0,
    )
    assert isinstance(rotor_aero, RotorAerodynamics)
    assert rotor_aero.thrust > 0.0
    assert rotor_aero.torque > 0.0
    assert rotor_aero.power > 0.0

    performance = calculate_rotor_performance(
        rotor_aero=rotor_aero,
        gross_weight=5000.0,
        engine_power=1000.0,
        drag_coefficient=0.02,
        parasite_area=10.0,
        fuel_capacity=500.0,
        sfc=0.5,
        altitude_m=0.0,
    )
    assert isinstance(performance, RotorPerformance)
    assert performance.hover_ceiling >= 0.0
    assert performance.max_forward_speed > 0.0
    assert performance.climb_rate >= 0.0
    assert performance.endurance >= 0.0
    assert performance.range >= 0.0

    envelope = calculate_rotor_performance_envelope(
        rotor_diameter=10.0,
        rotor_speed_rpm=300.0,
        blade_pitch_deg=10.0,
        num_blades=4,
        gross_weight_range=[4000.0, 5000.0, 6000.0],
        engine_power_range=[800.0, 1000.0, 1200.0],
        altitude_range=[0.0, 3000.0, 6000.0],
        drag_coefficient=0.02,
        parasite_area=10.0,
        fuel_capacity=500.0,
        sfc=0.5,
        isa_delta_c=0.0,
    )
    assert len(envelope["gross_weight"]) == 3
    assert len(envelope["engine_power"]) == 3
    assert len(envelope["altitude_m"]) == 3

    power_required = calculate_rotor_power_required(
        gross_weight=5000.0,
        climb_rate=5.0,
        drag_coefficient=0.02,
        parasite_area=10.0,
        altitude_m=0.0,
    )
    assert power_required > 0.0

    disk_loading = calculate_rotor_disk_loading(
        thrust=rotor_aero.thrust,
        rotor_diameter=10.0,
    )
    assert disk_loading > 0.0

    power_loading = calculate_rotor_power_loading(
        power=rotor_aero.power,
        rotor_diameter=10.0,
    )
    assert power_loading > 0.0


def test_openvsp_integration():
    """测试OpenVSP与SKILL集成"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )

    h_tail = create_horizontal_tail(
        area=8.0,
        aspect_ratio=5.0,
        taper_ratio=0.5,
        sweep_quarter_chord=30.0,
    )

    v_tail = create_vertical_tail(
        area=5.0,
        aspect_ratio=2.0,
        taper_ratio=0.6,
        sweep_quarter_chord=35.0,
    )

    aircraft = assemble_aircraft(
        wing=wing,
        fuselage=fuselage,
        h_tail=h_tail,
        v_tail=v_tail,
    )

    plate = degenerate_wing_to_plate(
        wing=wing,
        num_chordwise=10,
        num_spanwise=5,
    )

    mesh = generate_surface_mesh(
        geometry=plate,
        num_u=10,
        num_v=5,
    )

    result = calculate_parasite_drag_enhanced(
        geometry=wing,
        velocity=200.0,
        altitude_m=10000.0,
        sref=30.0,
    )

    aero_loads = calculate_aerodynamic_loads(
        geometry=aircraft,
        velocity=200.0,
        altitude_m=10000.0,
        alpha_deg=0.0,
    )

    inertial_loads = calculate_inertial_loads(
        mass=10000.0,
        cg=np.array([0.0, 0.0, 0.0]),
        acceleration=np.array([0.0, 0.0, 9.81]),
    )

    struct_loads = calculate_structural_loads(
        geometry=aircraft,
        aerodynamic_loads=aero_loads,
        inertial_loads=inertial_loads,
        material_yield_strength=270.0e6,
        safety_factor=1.5,
    )

    assert aircraft.wing == wing
    assert mesh.x.shape[0] == 10
    assert result.cd0_total > 0.0
    assert aero_loads.lift > 0.0
    assert struct_loads.safety_factor > 1.0


def test_end_to_end():
    """测试端到端流程"""
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )

    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )

    h_tail = create_horizontal_tail(
        area=8.0,
        aspect_ratio=5.0,
        taper_ratio=0.5,
        sweep_quarter_chord=30.0,
    )

    v_tail = create_vertical_tail(
        area=5.0,
        aspect_ratio=2.0,
        taper_ratio=0.6,
        sweep_quarter_chord=35.0,
    )

    aircraft = assemble_aircraft(
        wing=wing,
        fuselage=fuselage,
        h_tail=h_tail,
        v_tail=v_tail,
    )

    plate = degenerate_wing_to_plate(
        wing=wing,
        num_chordwise=10,
        num_spanwise=5,
    )

    mesh = generate_surface_mesh(
        geometry=plate,
        num_u=10,
        num_v=5,
    )

    result = calculate_parasite_drag_enhanced(
        geometry=wing,
        velocity=200.0,
        altitude_m=10000.0,
        sref=30.0,
    )

    aero_loads = calculate_aerodynamic_loads(
        geometry=aircraft,
        velocity=200.0,
        altitude_m=10000.0,
        alpha_deg=0.0,
    )

    inertial_loads = calculate_inertial_loads(
        mass=10000.0,
        cg=np.array([0.0, 0.0, 0.0]),
        acceleration=np.array([0.0, 0.0, 9.81]),
    )

    struct_loads = calculate_structural_loads(
        geometry=aircraft,
        aerodynamic_loads=aero_loads,
        inertial_loads=inertial_loads,
        material_yield_strength=270.0e6,
        safety_factor=1.5,
    )

    assert aircraft.wing.area == 30.0
    assert mesh.x.shape[0] == 10
    assert result.cd0_total > 0.0
    assert aero_loads.lift > 0.0
    assert struct_loads.safety_factor > 1.0
    assert aircraft.fuselage.length == 15.0
    assert aircraft.h_tail.area == 8.0
    assert aircraft.v_tail.area == 5.0


if __name__ == "__main__":
    pytest.main([__file__])

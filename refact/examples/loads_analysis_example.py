from aircraft_design.class3_detailed.loads_analysis import (
    calculate_aerodynamic_loads,
    calculate_inertial_loads,
    calculate_structural_loads,
    calculate_load_envelope,
    calculate_flutter_analysis,
)
from aircraft_design.class2_preliminary.geometry_modeling import (
    create_wing,
    create_fuselage,
    assemble_aircraft,
)
import numpy as np


def main():
    print("载荷分析使用示例")
    print("=" * 50)

    print("\n1. 创建飞机")
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
        h_tail=None,
        v_tail=None,
    )
    print("   飞机创建完成")
    print(f"   机翼参考面积: {aircraft.wing.area:.2f} m²")
    print(f"   机身长度: {aircraft.fuselage.length:.2f} m")

    print("\n2. 计算气动载荷")
    aero_loads = calculate_aerodynamic_loads(
        geometry=aircraft,
        velocity=200.0,
        altitude_m=10000.0,
        alpha_deg=0.0,
        beta_deg=0.0,
        sref=30.0,
    )
    print("   气动载荷计算完成")
    print(f"   升力: {aero_loads.lift:.2f} N")
    print(f"   阻力: {aero_loads.drag:.2f} N")
    print(f"   俯仰力矩: {aero_loads.moment_pitch:.2f} N·m")
    print(f"   滚转力矩: {aero_loads.moment_roll:.2f} N·m")
    print(f"   偏航力矩: {aero_loads.moment_yaw:.2f} N·m")
    print(f"   升力系数 CL: {aero_loads.cl:.4f}")
    print(f"   阻力系数 CD: {aero_loads.cd:.4f}")
    print(f"   俯仰力矩系数 CM: {aero_loads.cm:.4f}")

    print("\n3. 计算惯性载荷")
    inertial_loads = calculate_inertial_loads(
        mass=10000.0,
        cg=np.array([0.0, 0.0, 0.0]),
        acceleration=np.array([0.0, 0.0, 9.81]),
    )
    print("   惯性载荷计算完成")
    print(f"   质量: {inertial_loads.mass:.2f} kg")
    print(f"   重心: ({inertial_loads.cg[0]:.2f}, {inertial_loads.cg[1]:.2f}, {inertial_loads.cg[2]:.2f}) m")
    print(
        f"   加速度: ({inertial_loads.acceleration[0]:.2f}, {inertial_loads.acceleration[1]:.2f}, {inertial_loads.acceleration[2]:.2f}) m/s²"
    )
    print(f"   惯性力: ({inertial_loads.force[0]:.2f}, {inertial_loads.force[1]:.2f}, {inertial_loads.force[2]:.2f}) N")
    print(
        f"   惯性力矩: ({inertial_loads.moment[0]:.2f}, {inertial_loads.moment[1]:.2f}, {inertial_loads.moment[2]:.2f}) N·m"
    )

    print("\n4. 计算结构载荷")
    struct_loads = calculate_structural_loads(
        geometry=aircraft,
        aerodynamic_loads=aero_loads,
        inertial_loads=inertial_loads,
        material_yield_strength=270.0e6,
        safety_factor=1.5,
    )
    print("   结构载荷计算完成")
    print(f"   最大弯矩: {np.max(np.abs(struct_loads.bending_moment)):.2f} N·m")
    print(f"   最大剪力: {np.max(np.abs(struct_loads.shear_force)):.2f} N")
    print(f"   扭矩: {struct_loads.torque:.2f} N·m")
    print(f"   冯·米塞斯应力: {struct_loads.von_mises_stress:.2e} Pa")
    print(f"   安全系数: {struct_loads.safety_factor:.2f}")

    print("\n5. 载荷包络")
    envelope = calculate_load_envelope(
        geometry=aircraft,
        velocity_range=[100.0, 150.0, 200.0],
        altitude_range=[0.0, 5000.0, 10000.0],
        alpha_range=[0.0, 5.0],
        material_yield_strength=270.0e6,
        safety_factor=1.5,
    )
    print("   载荷包络计算完成")
    print(f"   速度范围: {envelope['velocity']} m/s")
    print(f"   高度范围: {envelope['altitude_m']} m")
    print(f"   攻角范围: {envelope['alpha']} deg")

    print("\n6. 颤振分析")
    flutter = calculate_flutter_analysis(
        geometry=aircraft,
        velocity=200.0,
        altitude_m=10000.0,
    )
    print("   颤振分析完成")
    print(f"   颤振频率: {flutter['flutter_frequency_hz']:.2f} Hz")
    print(f"   颤振速度: {flutter['flutter_velocity_m_s']:.2f} m/s")
    print(f"   颤振角速度: {flutter['flutter_angular_velocity_rad_s']:.2f} rad/s")

    print("\n" + "=" * 50)
    print("载荷分析使用示例完成")


if __name__ == "__main__":
    main()

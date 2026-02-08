from aircraft_design.parasite_drag_enhanced import (
    calculate_parasite_drag_enhanced,
    calculate_parasite_drag_sweep,
    generate_parasite_drag_envelope,
)
from aircraft_design.geometry_modeling import create_wing


def main():
    print("寄生阻力使用示例")
    print("=" * 50)

    print("\n1. 创建机翼")
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
    )
    print("   机翼创建完成")
    print(f"   参考面积: {wing.area:.2f} m²")
    print(f"   翼展: {wing.span:.2f} m")

    print("\n2. 计算寄生阻力")
    result = calculate_parasite_drag_enhanced(
        geometry=wing,
        velocity=200.0,
        altitude_m=10000.0,
        sref=30.0,
        surface_roughness=0.0,
        isa_delta_c=0.0,
    )
    print("   寄生阻力计算完成")
    print(f"   总阻力系数 CD0: {result.cd0_total:.6f}")
    print(f"   摩擦阻力系数 CD0_fric: {result.cd0_fric:.6f}")
    print(f"   形状阻力系数 CD0_form: {result.cd0_form:.6f}")
    print(f"   干扰阻力系数 CD0_interf: {result.cd0_interf:.6f}")
    print(f"   雷诺数: {result.reynolds_number:.2e}")
    print(f"   层流摩擦系数: {result.cf_laminar:.6f}")
    print(f"   湍流摩擦系数: {result.cf_turbulent:.6f}")

    print("\n3. 寄生阻力扫描")
    sweep_result = calculate_parasite_drag_sweep(
        geometry=wing,
        velocity_range=[100.0, 150.0, 200.0],
        altitude_range=[0.0, 5000.0, 10000.0],
        sref=30.0,
        surface_roughness=0.0,
        isa_delta_c=0.0,
    )
    print("   寄生阻力扫描完成")
    print(f"   速度范围: {sweep_result['velocity']}")
    print(f"   高度范围: {sweep_result['altitude']} m")
    for i, velocity in enumerate(sweep_result["velocity"]):
        for j, altitude in enumerate(sweep_result["altitude"]):
            cd0_total = sweep_result["cd0_total"][i][j]
            print(f"   速度={velocity:.0f} m/s, 高度={altitude:.0f} m: CD0={cd0_total:.6f}")

    print("\n4. 寄生阻力包络")
    envelope = generate_parasite_drag_envelope(
        geometry=wing,
        sref=30.0,
        mach_range=[0.3, 0.5, 0.7],
        altitude_range=[0.0, 5000.0, 10000.0],
        surface_roughness=0.0,
        isa_delta_c=0.0,
    )
    print("   寄生阻力包络生成完成")
    print(f"   马赫数范围: {envelope['mach']}")
    print(f"   高度范围: {envelope['altitude_m']} m")
    for i, mach in enumerate(envelope["mach"]):
        for j, altitude in enumerate(envelope["altitude_m"]):
            cd0_total = envelope["cd0_total"][i][j]
            print(f"   马赫数={mach:.2f}, 高度={altitude:.0f} m: CD0={cd0_total:.6f}")

    print("\n" + "=" * 50)
    print("寄生阻力使用示例完成")


if __name__ == "__main__":
    main()

from aircraft_design.rotorcraft_analysis import (
    calculate_rotor_aerodynamics,
    calculate_rotor_performance,
    calculate_rotor_performance_envelope,
    calculate_rotor_power_required,
    calculate_rotor_disk_loading,
    calculate_rotor_power_loading,
)


def main():
    print("旋翼机分析使用示例")
    print("=" * 50)

    print("\n1. 计算旋翼气动力")
    rotor_aero = calculate_rotor_aerodynamics(
        rotor_diameter=10.0,
        rotor_speed_rpm=300.0,
        blade_pitch_deg=10.0,
        num_blades=4,
        air_density=1.225,
        altitude_m=0.0,
        isa_delta_c=0.0,
    )
    print("   旋翼气动力计算完成")
    print(f"   推力: {rotor_aero.thrust:.2f} N")
    print(f"   扭矩: {rotor_aero.torque:.2f} N·m")
    print(f"   功率: {rotor_aero.power:.2f} W")
    print(f"   诱导速度: {rotor_aero.induced_velocity:.2f} m/s")
    print(f"   功重比: {rotor_aero.figure_of_merit:.4f} N/W")
    print(f"   功率载荷: {rotor_aero.power_loading:.2f} W/m²")
    print(f"   盘载荷: {rotor_aero.disk_loading:.2f} N/m²")

    print("\n2. 计算旋翼性能")
    performance = calculate_rotor_performance(
        rotor_aero=rotor_aero,
        gross_weight=5000.0,
        engine_power=1000.0,
        drag_coefficient=0.02,
        parasite_area=10.0,
        fuel_capacity=500.0,
        sfc=0.5,
        altitude_m=0.0,
        isa_delta_c=0.0,
    )
    print("   旋翼性能计算完成")
    print(f"   悬停升限: {performance.hover_ceiling:.2f} m")
    print(f"   最大前飞速度: {performance.max_forward_speed:.2f} m/s")
    print(f"   爬升率: {performance.climb_rate:.2f} m/min")
    print(f"   续航: {performance.endurance:.2f} s")
    print(f"   航程: {performance.range:.2f} km")
    print(f"   实用升限: {performance.service_ceiling:.2f} m")
    print(f"   最大连续功率: {performance.max_continuous_power:.2f} W")

    print("\n3. 旋翼性能包络")
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
    print("   旋翼性能包络计算完成")
    print(f"   总重范围: {envelope['gross_weight']} kg")
    print(f"   发动机功率范围: {envelope['engine_power']} W")
    print(f"   高度范围: {envelope['altitude_m']} m")

    print("\n4. 计算旋翼所需功率")
    power_required = calculate_rotor_power_required(
        gross_weight=5000.0,
        climb_rate=5.0,
        drag_coefficient=0.02,
        parasite_area=10.0,
        altitude_m=0.0,
        isa_delta_c=0.0,
    )
    print("   旋翼所需功率计算完成")
    print(f"   所需功率: {power_required:.2f} W")

    print("\n5. 计算旋翼盘载荷")
    disk_loading = calculate_rotor_disk_loading(
        thrust=rotor_aero.thrust,
        rotor_diameter=10.0,
    )
    print("   旋翼盘载荷计算完成")
    print(f"   盘载荷: {disk_loading:.2f} N/m²")

    print("\n6. 计算旋翼功率载荷")
    power_loading = calculate_rotor_power_loading(
        power=rotor_aero.power,
        rotor_diameter=10.0,
    )
    print("   旋翼功率载荷计算完成")
    print(f"   功率载荷: {power_loading:.2f} W/m²")

    print("\n" + "=" * 50)
    print("旋翼机分析使用示例完成")


if __name__ == "__main__":
    main()

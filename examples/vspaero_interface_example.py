from aircraft_design.vspaero_interface import (
    generate_vspaero_input,
    parse_vspaero_output,
    calculate_lift_distribution,
    calculate_drag_distribution,
    calculate_moment_coefficients,
    generate_vspaero_sweep,
)
from aircraft_design.geometry_modeling import (
    create_wing,
    create_fuselage,
    create_horizontal_tail,
    create_vertical_tail,
    assemble_aircraft,
)


def main():
    print("VSPAERO接口使用示例")
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
    print("   飞机创建完成")
    print(f"   机翼参考面积: {aircraft.wing.area:.2f} m²")
    print(f"   机身长度: {aircraft.fuselage.length:.2f} m")
    print(f"   平尾面积: {aircraft.h_tail.area:.2f} m²")
    print(f"   垂尾面积: {aircraft.v_tail.area:.2f} m²")

    print("\n2. 生成VSPAERO输入文件")
    input_file = "vspaero_input.txt"
    generate_vspaero_input(
        geometry=aircraft,
        output_file=input_file,
        mach=0.7,
        alpha_deg=0.0,
        beta_deg=0.0,
        num_spanwise=20,
        num_chordwise=10,
    )
    print("   VSPAERO输入文件生成完成")
    print(f"   文件名: {input_file}")

    print("\n3. 模拟VSPAERO输出")
    from aircraft_design.vspaero_interface import VSPAEROResult

    mock_result = VSPAEROResult(
        cl=0.5,
        cd=0.03,
        cm=-0.1,
        cn=0.0,
        cy=0.0,
        cl_alpha=5.5,
        cd_alpha=0.2,
        lift_distribution={0.0: 0.1, 0.5: 0.2, 1.0: 0.15},
        drag_distribution={0.0: 0.01, 0.5: 0.02, 1.0: 0.015},
        moment_coefficients={"CM": -0.1, "CR": 0.0, "CY": 0.0},
    )

    print("\n4. 解析VSPAERO输出")
    output_file = "vspaero_output.txt"
    parsed_result = parse_vspaero_output(output_file=output_file)
    print("   VSPAERO输出解析完成")
    print(f"   升力系数 CL: {parsed_result.cl:.4f}")
    print(f"   阻力系数 CD: {parsed_result.cd:.4f}")
    print(f"   俯仰力矩系数 CM: {parsed_result.cm:.4f}")

    print("\n5. 计算升力分布")
    lift_dist = calculate_lift_distribution(
        vspaero_results=mock_result,
        geometry=aircraft,
    )
    print("   升力分布计算完成")
    print(f"   展向位置: {list(lift_dist['spanwise_location'].values())}")
    print(f"   升力系数: {list(lift_dist['lift_coefficient'].values())}")
    print(f"   总升力: {lift_dist['total_lift']:.2f}")

    print("\n6. 计算阻力分布")
    drag_dist = calculate_drag_distribution(
        vspaero_results=mock_result,
        geometry=aircraft,
    )
    print("   阻力分布计算完成")
    print(f"   展向位置: {list(drag_dist['spanwise_location'].values())}")
    print(f"   阻力系数: {list(drag_dist['drag_coefficient'].values())}")
    print(f"   总阻力: {drag_dist['total_drag']:.2f}")

    print("\n7. 计算力矩系数")
    moments = calculate_moment_coefficients(vspaero_results=mock_result)
    print("   力矩系数计算完成")
    print(f"   俯仰力矩: {moments['pitch_moment']:.4f}")
    print(f"   滚转力矩: {moments['roll_moment']:.4f}")
    print(f"   偏航力矩: {moments['yaw_moment']:.4f}")

    print("\n8. VSPAERO扫描")
    sweep = generate_vspaero_sweep(
        geometry=aircraft,
        mach_range=[0.5, 0.7],
        alpha_range=[0.0, 5.0],
        output_prefix="vspaero_sweep",
    )
    print("   VSPAERO扫描生成完成")
    print(f"   马赫数范围: {sweep['mach']}")
    print(f"   攻角范围: {sweep['alpha']}")
    for i, mach in enumerate(sweep["mach"]):
        for j, alpha in enumerate(sweep["alpha"]):
            cl = sweep["cl"][i][j]
            cd = sweep["cd"][i][j]
            l_d = sweep["l_d"][i][j]
            print(f"   马赫数={mach:.2f}, 攻角={alpha:.2f} deg: CL={cl:.4f}, CD={cd:.4f}, L/D={l_d:.2f}")

    print("\n" + "=" * 50)
    print("VSPAERO接口使用示例完成")


if __name__ == "__main__":
    main()

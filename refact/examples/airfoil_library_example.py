from aircraft_design.config.airfoil_library import (
    generate_naca4_airfoil,
    generate_naca5_airfoil,
    generate_naca6_airfoil,
    scale_airfoil,
    generate_airfoil_library,
)


def main():
    print("翼型库使用示例")
    print("=" * 50)

    print("\n1. 生成NACA 4位数翼型")
    naca4 = generate_naca4_airfoil(
        max_camber=0.02,
        max_camber_location=0.4,
        max_thickness=0.12,
        num_points=100,
    )
    print("   NACA 4位数翼型生成完成")
    print(f"   最大厚度: {naca4.max_thickness:.4f}")
    print(f"   最大弯度: {naca4.max_camber:.4f}")
    print(f"   前缘半径: {naca4.leading_edge_radius:.6f}")

    print("\n2. 生成NACA 5位数翼型")
    naca5 = generate_naca5_airfoil(
        design_lift_coeff=0.3,
        max_thickness=0.12,
        num_points=100,
    )
    print("   NACA 5位数翼型生成完成")
    print(f"   最大厚度: {naca5.max_thickness:.4f}")
    print(f"   最大弯度: {naca5.max_camber:.4f}")

    print("\n3. 生成NACA 6系列翼型")
    naca6 = generate_naca6_airfoil(
        series_char="63",
        max_thickness=0.12,
        design_lift_coeff=0.3,
        num_points=100,
    )
    print("   NACA 6系列翼型生成完成")
    print(f"   最大厚度: {naca6.max_thickness:.4f}")
    print(f"   最大弯度: {naca6.max_camber:.4f}")

    print("\n4. 翼型缩放")
    scaled_naca4 = scale_airfoil(
        airfoil=naca4,
        chord=1.5,
    )
    print("   翼型缩放完成")
    print(f"   弦长: {scaled_naca4.chord:.2f} m")
    print(f"   最大厚度: {scaled_naca4.max_thickness:.4f} m")

    print("\n5. 生成翼型库")
    library = generate_airfoil_library(
        naca4_params=[
            {"max_camber": 0.02, "max_camber_location": 0.4, "max_thickness": 0.12},
            {"max_camber": 0.0, "max_camber_location": 0.4, "max_thickness": 0.12},
        ],
        naca5_params=[
            {"design_lift_coeff": 0.3, "max_thickness": 0.12},
        ],
        naca6_params=[
            {"series_char": "63", "max_thickness": 0.12, "design_lift_coeff": 0.3},
            {"series_char": "64", "max_thickness": 0.12, "design_lift_coeff": 0.4},
        ],
    )
    print("   翼型库生成完成")
    print(f"   翼型数量: {len(library)}")
    for name, airfoil in library.items():
        print(f"   - {name}: 最大厚度={airfoil.max_thickness:.4f}, 最大弯度={airfoil.max_camber:.4f}")

    print("\n" + "=" * 50)
    print("翼型库使用示例完成")


if __name__ == "__main__":
    main()

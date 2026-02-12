from aircraft_design.class2_preliminary.degenerate_geometry import (
    degenerate_wing_to_plate,
    degenerate_wing_to_stick,
    degenerate_fuselage_to_cylinder,
    degenerate_propeller_to_disk,
    calculate_mass_properties,
)
from aircraft_design.class2_preliminary.geometry_modeling import (
    create_wing,
    create_fuselage,
)
import numpy as np


def main():
    print("退化几何使用示例")
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

    print("\n2. 将机翼退化为平板")
    plate = degenerate_wing_to_plate(
        wing=wing,
        num_chordwise=10,
        num_spanwise=5,
    )
    print("   平板退化完成")
    print(f"   网格尺寸: {plate.x.shape[0]} x {plate.x.shape[1]}")
    print(f"   总面积: {np.sum(plate.area):.2f} m²")

    print("\n3. 将机翼退化为梁")
    stick = degenerate_wing_to_stick(
        wing=wing,
        num_sections=10,
    )
    print("   梁退化完成")
    print(f"   截面数量: {len(stick.le)}")

    print("\n4. 创建机身")
    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
    )
    print("   机身创建完成")
    print(f"   长度: {fuselage.length:.2f} m")
    print(f"   直径: {fuselage.diameter:.2f} m")

    print("\n5. 将机身退化为圆柱")
    cylinder = degenerate_fuselage_to_cylinder(
        fuselage=fuselage,
        num_sections=20,
    )
    print("   圆柱退化完成")
    print(f"   网格尺寸: {cylinder.x.shape[0]} x {cylinder.x.shape[1]}")
    print(f"   总面积: {np.sum(cylinder.area):.2f} m²")

    print("\n6. 将螺旋桨退化为圆盘")
    disk = degenerate_propeller_to_disk(
        diameter=2.0,
        position=np.array([5.0, 0.0, 0.0]),
        normal=np.array([0.0, 0.0, 1.0]),
    )
    print("   圆盘退化完成")
    print(f"   直径: {disk.diameter:.2f} m")

    print("\n7. 计算质量属性")
    mass_props = calculate_mass_properties(
        geometry=plate,
        density=2700.0,
    )
    print("   质量属性计算完成")
    print(f"   面积: {mass_props.area:.2f} m²")
    print(f"   体积: {mass_props.volume:.4f} m³")
    print(f"   质量: {mass_props.mass:.2f} kg")
    print(f"   重心: ({mass_props.centroid[0]:.2f}, {mass_props.centroid[1]:.2f}, {mass_props.centroid[2]:.2f}) m")
    print(f"   惯性矩 Ixx: {mass_props.ixx:.2f} kg·m²")
    print(f"   惯性矩 Iyy: {mass_props.iyy:.2f} kg·m²")
    print(f"   惯性矩 Izz: {mass_props.izz:.2f} kg·m²")

    print("\n" + "=" * 50)
    print("退化几何使用示例完成")


if __name__ == "__main__":
    main()

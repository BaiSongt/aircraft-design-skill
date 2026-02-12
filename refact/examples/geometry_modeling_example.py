from aircraft_design.class2_preliminary.geometry_modeling import (
    create_wing,
    create_fuselage,
    create_horizontal_tail,
    create_vertical_tail,
    create_engine,
    create_landing_gear,
    assemble_aircraft,
    translate_geometry,
    rotate_geometry,
    scale_geometry,
    mirror_geometry,
)
import numpy as np


def main():
    print("几何建模使用示例")
    print("=" * 50)

    print("\n1. 创建机翼")
    wing = create_wing(
        area=30.0,
        aspect_ratio=8.0,
        taper_ratio=0.6,
        sweep_quarter_chord=25.0,
        twist_root=0.0,
        twist_tip=-2.0,
        dihedral=5.0,
        incidence=2.0,
        airfoil_root="NACA0012",
        airfoil_tip="NACA0012",
        position=np.array([0.0, 0.0, 0.0]),
    )
    print("   机翼创建完成")
    print(f"   参考面积: {wing.area:.2f} m²")
    print(f"   翼展: {wing.span:.2f} m")
    print(f"   根弦长: {wing.chord_root:.2f} m")
    print(f"   梢弦长: {wing.chord_tip:.2f} m")
    print(f"   后掠角: {wing.sweep_quarter_chord:.2f} deg")
    print(f"   梯形比: {wing.taper_ratio:.2f}")

    print("\n2. 创建机身")
    fuselage = create_fuselage(
        length=15.0,
        diameter=2.0,
        fineness_ratio=7.5,
        nose_length=4.5,
        tail_length=4.5,
        position=np.array([0.0, 0.0, 0.0]),
    )
    print("   机身创建完成")
    print(f"   长度: {fuselage.length:.2f} m")
    print(f"   直径: {fuselage.diameter:.2f} m")
    print(f"   长径比: {fuselage.fineness_ratio:.2f}")

    print("\n3. 创建平尾")
    h_tail = create_horizontal_tail(
        area=8.0,
        aspect_ratio=5.0,
        taper_ratio=0.5,
        sweep_quarter_chord=30.0,
        incidence=0.0,
        airfoil="NACA0012",
        position=np.array([-5.0, 0.0, 0.0]),
    )
    print("   平尾创建完成")
    print(f"   参考面积: {h_tail.area:.2f} m²")
    print(f"   翼展: {h_tail.span:.2f} m")

    print("\n4. 创建垂尾")
    v_tail = create_vertical_tail(
        area=5.0,
        aspect_ratio=2.0,
        taper_ratio=0.6,
        sweep_quarter_chord=35.0,
        airfoil="NACA0012",
        position=np.array([-5.0, 0.0, 0.0]),
    )
    print("   垂尾创建完成")
    print(f"   参考面积: {v_tail.area:.2f} m²")
    print(f"   翼展: {v_tail.span:.2f} m")

    print("\n5. 创建发动机")
    engine = create_engine(
        diameter=1.5,
        length=3.0,
        bypass_ratio=6.0,
        position=np.array([2.0, 2.5, -0.5]),
        orientation=np.array([0.0, 0.0, 0.0]),
    )
    print("   发动机创建完成")
    print(f"   直径: {engine.diameter:.2f} m")
    print(f"   长度: {engine.length:.2f} m")
    print(f"   涵道比: {engine.bypass_ratio:.2f}")

    print("\n6. 创建起落架")
    landing_gear = create_landing_gear(
        type="tricycle",
        position=np.array([0.0, 0.0, -1.5]),
        height=1.5,
        track_width=3.0,
    )
    print("   起落架创建完成")
    print(f"   类型: {landing_gear.type}")
    print(f"   高度: {landing_gear.height:.2f} m")
    print(f"   轮距: {landing_gear.track_width:.2f} m")

    print("\n7. 组装飞机")
    aircraft = assemble_aircraft(
        wing=wing,
        fuselage=fuselage,
        h_tail=h_tail,
        v_tail=v_tail,
        engines=[engine],
        landing_gear=[landing_gear],
    )
    print("   飞机组装完成")
    print(f"   机翼参考面积: {aircraft.wing.area:.2f} m²")
    print(f"   机身长度: {aircraft.fuselage.length:.2f} m")
    print(f"   平尾面积: {aircraft.h_tail.area:.2f} m²")
    print(f"   垂尾面积: {aircraft.v_tail.area:.2f} m²")
    print(f"   发动机数量: {len(aircraft.engines)}")
    print(f"   起落架数量: {len(aircraft.landing_gear)}")

    print("\n8. 几何变换")
    print("   8.1 平移几何")
    translated_wing = translate_geometry(
        geometry=wing,
        dx=1.0,
        dy=0.0,
        dz=0.0,
    )
    print("       平移完成")
    print(f"       原位置: {wing.position}")
    print(f"       新位置: {translated_wing.position}")

    print("   8.2 旋转几何")
    rotate_geometry(
        geometry=wing,
        axis="z",
        angle_deg=10.0,
    )
    print("       旋转完成")
    print("       旋转角度: 10.0 deg")

    print("   8.3 缩放几何")
    scaled_wing = scale_geometry(
        geometry=wing,
        scale_factor=1.1,
    )
    print("       缩放完成")
    print(f"       原面积: {wing.area:.2f} m²")
    print(f"       新面积: {scaled_wing.area:.2f} m²")

    print("   8.4 镜像几何")
    mirror_geometry(
        geometry=wing,
        axis="y",
    )
    print("       镜像完成")
    print("       镜像轴: y")

    print("\n" + "=" * 50)
    print("几何建模使用示例完成")


if __name__ == "__main__":
    main()

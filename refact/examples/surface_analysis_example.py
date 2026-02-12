from aircraft_design.class2_preliminary.surface_analysis import (
    generate_surface_mesh,
    calculate_normals,
    calculate_curvature,
    calculate_surface_area,
    calculate_surface_centroid,
    calculate_surface_volume,
)
from aircraft_design.class2_preliminary.degenerate_geometry import degenerate_wing_to_plate
from aircraft_design.class2_preliminary.geometry_modeling import create_wing
import numpy as np


def main():
    print("表面分析使用示例")
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

    print("\n3. 生成表面网格")
    mesh = generate_surface_mesh(
        geometry=plate,
        num_u=10,
        num_v=5,
    )
    print("   表面网格生成完成")
    print(f"   网格尺寸: {mesh.x.shape[0]} x {mesh.x.shape[1]}")

    print("\n4. 计算法向量")
    normals = calculate_normals(mesh=mesh)
    print("   法向量计算完成")
    print(f"   法向量数量: {len(normals.nx)}")

    print("\n5. 计算曲率")
    curvature = calculate_curvature(mesh=mesh)
    print("   曲率计算完成")
    print(
        f"   主曲率1范围: [{np.min(curvature.principal_curvature_1):.6f}, {np.max(curvature.principal_curvature_1):.6f}]"
    )
    print(
        f"   主曲率2范围: [{np.min(curvature.principal_curvature_2):.6f}, {np.max(curvature.principal_curvature_2):.6f}]"
    )
    print(f"   高斯曲率范围: [{np.min(curvature.gaussian_curvature):.6f}, {np.max(curvature.gaussian_curvature):.6f}]")
    print(f"   平均曲率范围: [{np.min(curvature.mean_curvature):.6f}, {np.max(curvature.mean_curvature):.6f}]")

    print("\n6. 计算表面积")
    area = calculate_surface_area(mesh=mesh)
    print("   表面积计算完成")
    print(f"   表面积: {area:.2f} m²")

    print("\n7. 计算表面重心")
    centroid = calculate_surface_centroid(mesh=mesh)
    print("   表面重心计算完成")
    print(f"   重心: ({centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f}) m")

    print("\n8. 计算表面体积")
    volume = calculate_surface_volume(mesh=mesh)
    print("   表面体积计算完成")
    print(f"   体积: {volume:.4f} m³")

    print("\n" + "=" * 50)
    print("表面分析使用示例完成")


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class SurfaceMesh:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    nx: np.ndarray
    ny: np.ndarray
    nz: np.ndarray
    area: np.ndarray
    centroid: np.ndarray


@dataclass(frozen=True)
class CurvatureResult:
    principal_curvature_1: np.ndarray
    principal_curvature_2: np.ndarray
    gaussian_curvature: np.ndarray
    mean_curvature: np.ndarray
    principal_direction_1: np.ndarray
    principal_direction_2: np.ndarray


def generate_surface_mesh(
    *,
    geometry: Any,
    num_u: int = 20,
    num_v: int = 10,
) -> SurfaceMesh:
    if num_u < 2:
        raise ValueError("num_u must be >= 2.")
    if num_v < 2:
        raise ValueError("num_v must be >= 2.")

    if hasattr(geometry, "x") and hasattr(geometry, "y") and hasattr(geometry, "z"):
        x = geometry.x
        y = geometry.y
        z = geometry.z
    else:
        raise ValueError("geometry must have x, y, z attributes.")

    x_mesh = x
    y_mesh = y
    z_mesh = z

    dx_du = np.gradient(x_mesh, axis=0)
    dy_du = np.gradient(y_mesh, axis=0)
    dz_du = np.gradient(z_mesh, axis=0)

    dx_dv = np.gradient(x_mesh, axis=1)
    dy_dv = np.gradient(y_mesh, axis=1)
    dz_dv = np.gradient(z_mesh, axis=1)

    nx = dy_du * dz_dv - dz_du * dy_dv
    ny = dz_du * dx_dv - dx_du * dz_dv
    nz = dx_du * dy_dv - dy_du * dx_dv

    norm = sqrt(nx**2 + ny**2 + nz**2)
    nx = nx / norm
    ny = ny / norm
    nz = nz / norm

    dx = np.zeros_like(x_mesh)

    for i in range(x_mesh.shape[0] - 1):
        for j in range(x_mesh.shape[1] - 1):
            p1 = np.array([x_mesh[i, j], y_mesh[i, j], z_mesh[i, j]])
            p2 = np.array([x_mesh[i + 1, j], y_mesh[i + 1, j], z_mesh[i + 1, j]])
            p3 = np.array([x_mesh[i + 1, j + 1], y_mesh[i + 1, j + 1], z_mesh[i + 1, j + 1]])
            p4 = np.array([x_mesh[i, j + 1], y_mesh[i, j + 1], z_mesh[i, j + 1]])

            v1 = p2 - p1
            v2 = p3 - p1
            v3 = p4 - p1

            cross1 = np.cross(v1, v2)
            cross2 = np.cross(v3, v1)

            area1 = 0.5 * np.linalg.norm(cross1)
            area2 = 0.5 * np.linalg.norm(cross2)

            dx[i, j] = (area1 + area2) / 2.0

    centroid = np.array(
        [
            np.mean(x_mesh),
            np.mean(y_mesh),
            np.mean(z_mesh),
        ]
    )

    return SurfaceMesh(
        x=x_mesh,
        y=y_mesh,
        z=z_mesh,
        nx=nx,
        ny=ny,
        nz=nz,
        area=dx,
        centroid=centroid,
    )


def calculate_normals(
    *,
    mesh: SurfaceMesh,
) -> SurfaceMesh:
    dx_du = np.gradient(mesh.x, axis=0)
    dy_du = np.gradient(mesh.y, axis=0)
    dz_du = np.gradient(mesh.z, axis=0)

    dx_dv = np.gradient(mesh.x, axis=1)
    dy_dv = np.gradient(mesh.y, axis=1)
    dz_dv = np.gradient(mesh.z, axis=1)

    nx = dy_du * dz_dv - dz_du * dy_dv
    ny = dz_du * dx_dv - dx_du * dz_dv
    nz = dx_du * dy_dv - dy_du * dx_dv

    norm = sqrt(nx**2 + ny**2 + nz**2)
    nx = nx / norm
    ny = ny / norm
    nz = nz / norm

    return SurfaceMesh(
        x=mesh.x,
        y=mesh.y,
        z=mesh.z,
        nx=nx,
        ny=ny,
        nz=nz,
        area=mesh.area,
        centroid=mesh.centroid,
    )


def calculate_curvature(
    *,
    mesh: SurfaceMesh,
) -> CurvatureResult:
    dx_du = np.gradient(mesh.x, axis=0)
    dy_du = np.gradient(mesh.y, axis=0)
    dz_du = np.gradient(mesh.z, axis=0)

    dx_dv = np.gradient(mesh.x, axis=1)
    dy_dv = np.gradient(mesh.y, axis=1)
    dz_dv = np.gradient(mesh.z, axis=1)

    d2x_du2 = np.gradient(dx_du, axis=0)
    d2y_du2 = np.gradient(dy_du, axis=0)
    d2z_du2 = np.gradient(dz_du, axis=0)

    d2x_dv2 = np.gradient(dx_dv, axis=1)
    d2y_dv2 = np.gradient(dy_dv, axis=1)
    d2z_dv2 = np.gradient(dz_dv, axis=1)

    d2x_dudv = np.gradient(dx_du, axis=1)
    d2y_dudv = np.gradient(dy_du, axis=1)
    d2z_dudv = np.gradient(dz_du, axis=1)

    E = 1.0 + dx_du**2 + dy_du**2 + dz_du**2

    L = d2x_du2 + d2y_du2 + d2z_du2
    M = d2x_dudv * dx_dv + d2y_dudv * dy_dv + d2z_dudv * dz_dv
    N = d2x_dv2 + d2y_dv2 + d2z_dv2

    G = (L * N - M**2) / (E**2)

    H = (2 * E * L * N - 2 * E * M * M - L**2) / (E**3)

    k1 = G - sqrt(G**2 - H)
    k2 = G + sqrt(G**2 - H)

    principal_curvature_1 = k1
    principal_curvature_2 = k2

    gaussian_curvature = G
    mean_curvature = (principal_curvature_1 + principal_curvature_2) / 2.0

    principal_direction_1 = np.zeros_like(mesh.x)
    principal_direction_2 = np.zeros_like(mesh.x)

    for i in range(mesh.x.shape[0]):
        for j in range(mesh.x.shape[1]):
            if abs(k1[i, j]) > abs(k2[i, j]):
                principal_direction_1[i, j] = mesh.nx[i, j]
            else:
                principal_direction_1[i, j] = mesh.ny[i, j]

            if abs(k2[i, j]) > abs(k1[i, j]):
                principal_direction_2[i, j] = mesh.nx[i, j]
            else:
                principal_direction_2[i, j] = mesh.ny[i, j]

    return CurvatureResult(
        principal_curvature_1=principal_curvature_1,
        principal_curvature_2=principal_curvature_2,
        gaussian_curvature=gaussian_curvature,
        mean_curvature=mean_curvature,
        principal_direction_1=principal_direction_1,
        principal_direction_2=principal_direction_2,
    )


def calculate_surface_area(
    *,
    mesh: SurfaceMesh,
) -> float:
    return np.sum(mesh.area)


def calculate_surface_centroid(
    *,
    mesh: SurfaceMesh,
) -> np.ndarray:
    return mesh.centroid


def calculate_surface_volume(
    *,
    mesh: SurfaceMesh,
) -> float:
    x = mesh.x
    y = mesh.y
    z = mesh.z

    volume = 0.0

    for i in range(x.shape[0] - 1):
        for j in range(x.shape[1] - 1):
            p1 = np.array([x[i, j], y[i, j], z[i, j]])
            p2 = np.array([x[i + 1, j], y[i + 1, j], z[i + 1, j]])
            p3 = np.array([x[i + 1, j + 1], y[i + 1, j + 1], z[i + 1, j + 1]])
            p4 = np.array([x[i, j + 1], y[i, j + 1], z[i, j + 1]])

            v1 = p2 - p1
            v2 = p3 - p1
            v3 = p4 - p1

            cross1 = np.cross(v1, v2)
            cross2 = np.cross(v3, v1)

            area1 = 0.5 * np.linalg.norm(cross1)
            area2 = 0.5 * np.linalg.norm(cross2)

            avg_area = (area1 + area2) / 2.0
            avg_z = (p1[2] + p2[2] + p3[2] + p4[2]) / 4.0

            volume += avg_area * avg_z

    return volume


def generate_surface_mesh_from_geometry(
    *,
    geometry: Any,
    num_u: int = 20,
    num_v: int = 10,
) -> SurfaceMesh:
    if hasattr(geometry, "coordinates"):
        airfoil_coords = geometry.coordinates
        x = airfoil_coords.x
        y_upper = airfoil_coords.y[0]
        y_lower = airfoil_coords.y[1]

        u = np.linspace(0, 1, num_u)
        v = np.linspace(0, 1, num_v)

        _, v_grid = np.meshgrid(u, v, indexing="ij")
        chord_param = np.linspace(0, 1, len(x))
        x_interp = np.interp(u, chord_param, x)
        x_mesh = np.tile(x_interp[:, None], (1, num_v))
        y_mesh = np.zeros_like(x_mesh)
        z_mesh = np.zeros_like(x_mesh)

        for i in range(num_u):
            for j in range(num_v):
                y_upper_interp = np.interp(v_grid[i, j], x, y_upper)
                y_lower_interp = np.interp(v_grid[i, j], x, y_lower)

                if v_grid[i, j] <= 0.5:
                    y_mesh[i, j] = y_upper_interp
                    z_mesh[i, j] = 0.0
                else:
                    y_mesh[i, j] = y_lower_interp
                    z_mesh[i, j] = 0.0

        dx_du = np.gradient(x_mesh, axis=0)
        dy_du = np.gradient(y_mesh, axis=0)
        dz_du = np.gradient(z_mesh, axis=0)

        dx_dv = np.gradient(x_mesh, axis=1)
        dy_dv = np.gradient(y_mesh, axis=1)
        dz_dv = np.gradient(z_mesh, axis=1)

        nx = dy_du * dz_dv - dz_du * dy_dv
        ny = dz_du * dx_dv - dx_du * dz_dv
        nz = dx_du * dy_dv - dy_du * dx_dv

        norm = sqrt(nx**2 + ny**2 + nz**2)
        nx = nx / norm
        ny = ny / norm
        nz = nz / norm

        dx = np.zeros_like(x_mesh)

        for i in range(x_mesh.shape[0] - 1):
            for j in range(x_mesh.shape[1] - 1):
                p1 = np.array([x_mesh[i, j], y_mesh[i, j], z_mesh[i, j]])
                p2 = np.array([x_mesh[i + 1, j], y_mesh[i + 1, j], z_mesh[i + 1, j]])
                p3 = np.array([x_mesh[i + 1, j + 1], y_mesh[i + 1, j + 1], z_mesh[i + 1, j + 1]])
                p4 = np.array([x_mesh[i, j + 1], y_mesh[i, j + 1], z_mesh[i, j + 1]])

                v1 = p2 - p1
                v2 = p3 - p1
                v3 = p4 - p1

                cross1 = np.cross(v1, v2)
                cross2 = np.cross(v3, v1)

                area1 = 0.5 * np.linalg.norm(cross1)
                area2 = 0.5 * np.linalg.norm(cross2)

                dx[i, j] = (area1 + area2) / 2.0

        centroid = np.array(
            [
                np.mean(x_mesh),
                np.mean(y_mesh),
                np.mean(z_mesh),
            ]
        )

        return SurfaceMesh(
            x=x_mesh,
            y=y_mesh,
            z=z_mesh,
            nx=nx,
            ny=ny,
            nz=nz,
            area=dx,
            centroid=centroid,
        )
    else:
        raise ValueError("geometry must have coordinates attribute.")

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .geometry_modeling import WingGeometry, FuselageGeometry


@dataclass(frozen=True)
class DegenPlate:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    nx: np.ndarray
    ny: np.ndarray
    nz: np.ndarray
    area: np.ndarray
    centroid: np.ndarray


@dataclass(frozen=True)
class DegenStick:
    le: np.ndarray
    te: np.ndarray
    cg_shell: np.ndarray
    cg_solid: np.ndarray
    toc: float
    chord: np.ndarray
    i_shell: np.ndarray
    i_solid: np.ndarray
    sect_area: np.ndarray
    sect_normal: np.ndarray
    perim_top: np.ndarray
    perim_bot: np.ndarray
    u: np.ndarray
    transmat: np.ndarray
    invtransmat: np.ndarray
    toc2: float
    tloc2: float
    anglele: np.ndarray
    anglete: np.ndarray
    radle_top: np.ndarray
    radle_bot: np.ndarray
    sweeple: np.ndarray
    sweepte: np.ndarray
    area_top: np.ndarray
    area_bot: np.ndarray


@dataclass(frozen=True)
class DegenDisk:
    diameter: float
    position: np.ndarray
    normal: np.ndarray


@dataclass(frozen=True)
class MassProperties:
    area: float
    volume: float
    centroid: np.ndarray
    ixx: float
    iyy: float
    izz: float
    ixy: float
    ixz: float
    iyz: float
    mass: float


def degenerate_wing_to_plate(
    *,
    wing: WingGeometry,
    num_chordwise: int = 20,
    num_spanwise: int = 10,
) -> DegenPlate:
    if num_chordwise < 2:
        raise ValueError("num_chordwise must be >= 2.")
    if num_spanwise < 2:
        raise ValueError("num_spanwise must be >= 2.")

    u = np.linspace(0, 1, num_chordwise)
    w = np.linspace(0, 1, num_spanwise)

    u_grid, w_grid = np.meshgrid(u, w)

    chord_local = wing.chord_root + (wing.chord_tip - wing.chord_root) * w_grid
    twist_local = wing.twist_root + (wing.twist_tip - wing.twist_root) * w_grid

    x_local = u_grid * chord_local

    sweep_rad = wing.sweep_quarter_chord * pi / 180.0
    x_offset = (u_grid - 0.25) * chord_local * np.tan(sweep_rad)

    x = x_local * np.cos(twist_local) - x_offset * np.sin(twist_local)
    y = w_grid * wing.span / 2.0
    z = x_local * np.sin(twist_local) + x_offset * np.cos(twist_local)

    x = x + wing.position[0]
    y = y + wing.position[1]
    z = z + wing.position[2]

    dx_du = np.gradient(x, axis=0)
    dy_du = np.gradient(y, axis=0)
    dz_du = np.gradient(z, axis=0)

    dx_dw = np.gradient(x, axis=1)
    dy_dw = np.gradient(y, axis=1)
    dz_dw = np.gradient(z, axis=1)

    nx = dy_du * dz_dw - dz_du * dy_dw
    ny = dz_du * dx_dw - dx_du * dz_dw
    nz = dx_du * dy_dw - dy_du * dx_dw

    norm = sqrt(nx**2 + ny**2 + nz**2)
    nx = nx / norm
    ny = ny / norm
    nz = nz / norm

    dx_du = np.gradient(x, axis=0)
    dy_du = np.gradient(y, axis=0)
    dz_du = np.gradient(z, axis=0)

    dx_dw = np.gradient(x, axis=1)
    dy_dw = np.gradient(y, axis=1)
    dz_dw = np.gradient(z, axis=1)

    dx = np.zeros_like(x)
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

            dx[i, j] = (area1 + area2) / 2.0

    return DegenPlate(
        x=x,
        y=y,
        z=z,
        nx=nx,
        ny=ny,
        nz=nz,
        area=dx,
        centroid=np.array(
            [
                np.mean(x),
                np.mean(y),
                np.mean(z),
            ]
        ),
    )


def degenerate_wing_to_stick(
    *,
    wing: WingGeometry,
    num_sections: int = 10,
) -> DegenStick:
    if num_sections < 2:
        raise ValueError("num_sections must be >= 2.")

    u = np.linspace(0, 1, num_sections)

    chord_local = wing.chord_root + (wing.chord_tip - wing.chord_root) * u
    twist_local = wing.twist_root + (wing.twist_tip - wing.twist_root) * u

    sweep_rad = wing.sweep_quarter_chord * pi / 180.0
    x_offset = (u - 0.25) * chord_local * np.tan(sweep_rad)

    x_local = u * chord_local
    x = x_local * np.cos(twist_local) - x_offset * np.sin(twist_local)
    z = x_local * np.sin(twist_local) + x_offset * np.cos(twist_local)

    x = x + wing.position[0]
    z = z + wing.position[2]

    le = np.column_stack((x, np.zeros_like(x), z))
    te = np.column_stack((x, np.zeros_like(x), z))

    cg_shell = np.column_stack((x, np.zeros_like(x), z))
    cg_solid = np.column_stack((x, np.zeros_like(x), z))

    toc = wing.chord_root + wing.chord_tip
    chord = chord_local

    i_shell = np.zeros((num_sections, 3, 3))
    i_solid = np.zeros((num_sections, 3, 3))

    for i in range(num_sections):
        c = chord[i]
        i_shell[i, 0, 0] = (1.0 / 12.0) * c**3
        i_shell[i, 1, 1] = (1.0 / 12.0) * c**3
        i_shell[i, 2, 2] = (1.0 / 12.0) * c**3

        i_solid[i, 0, 0] = (1.0 / 36.0) * c**3
        i_solid[i, 1, 1] = (1.0 / 36.0) * c**3
        i_solid[i, 2, 2] = (1.0 / 36.0) * c**3

    sect_area = np.zeros(num_sections)
    sect_normal = np.zeros((num_sections, 3))

    for i in range(num_sections):
        c = chord[i]
        sect_area[i] = c * (wing.span / num_sections)
        sect_normal[i] = np.array([0.0, 0.0, 1.0])

    perim_top = np.zeros(num_sections)
    perim_bot = np.zeros(num_sections)

    for i in range(num_sections):
        c = chord[i]
        perim_top[i] = c
        perim_bot[i] = c

    u_array = u

    transmat = np.eye(4)
    invtransmat = np.eye(4)

    toc2 = toc
    tloc2 = 0.5

    anglele = np.zeros(num_sections)
    anglete = np.zeros(num_sections)

    for i in range(num_sections):
        anglele[i] = wing.sweep_quarter_chord
        anglete[i] = wing.sweep_quarter_chord

    radle_top = np.zeros(num_sections)
    radle_bot = np.zeros(num_sections)

    for i in range(num_sections):
        radle_top[i] = 0.0
        radle_bot[i] = 0.0

    sweeple = np.zeros(num_sections)
    sweepte = np.zeros(num_sections)

    for i in range(num_sections):
        sweeple[i] = wing.sweep_quarter_chord
        sweepte[i] = wing.sweep_quarter_chord

    area_top = np.zeros(num_sections)
    area_bot = np.zeros(num_sections)

    for i in range(num_sections):
        c = chord[i]
        area_top[i] = 0.5 * c * (wing.span / num_sections)
        area_bot[i] = 0.5 * c * (wing.span / num_sections)

    return DegenStick(
        le=le,
        te=te,
        cg_shell=cg_shell,
        cg_solid=cg_solid,
        toc=toc,
        chord=chord,
        i_shell=i_shell,
        i_solid=i_solid,
        sect_area=sect_area,
        sect_normal=sect_normal,
        perim_top=perim_top,
        perim_bot=perim_bot,
        u=u_array,
        transmat=transmat,
        invtransmat=invtransmat,
        toc2=toc2,
        tloc2=tloc2,
        anglele=anglele,
        anglete=anglete,
        radle_top=radle_top,
        radle_bot=radle_bot,
        sweeple=sweeple,
        sweepte=sweepte,
        area_top=area_top,
        area_bot=area_bot,
    )


def degenerate_fuselage_to_cylinder(
    *,
    fuselage: FuselageGeometry,
    num_sections: int = 20,
) -> DegenPlate:
    if num_sections < 2:
        raise ValueError("num_sections must be >= 2.")

    x = np.linspace(-fuselage.length / 2.0, fuselage.length / 2.0, num_sections)
    theta = np.linspace(0, 2 * pi, 50)

    x_grid, theta_grid = np.meshgrid(x, theta)

    y = (fuselage.diameter / 2.0) * np.cos(theta_grid)
    z = (fuselage.diameter / 2.0) * np.sin(theta_grid)

    x = x + fuselage.position[0]
    y = y + fuselage.position[1]
    z = z + fuselage.position[2]

    dx_dtheta = np.gradient(x, axis=1)
    dy_dtheta = np.gradient(y, axis=1)
    dz_dtheta = np.gradient(z, axis=1)

    dx_dx = np.gradient(x, axis=0)
    dy_dx = np.gradient(y, axis=0)
    dz_dx = np.gradient(z, axis=0)

    nx = dy_dtheta * dz_dx - dz_dtheta * dy_dx
    ny = dz_dtheta * dx_dx - dx_dtheta * dz_dx
    nz = dx_dtheta * dy_dx - dy_dtheta * dx_dx

    norm = sqrt(nx**2 + ny**2 + nz**2)
    nx = nx / norm
    ny = ny / norm
    nz = nz / norm

    dx = np.zeros_like(x)
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

            dx[i, j] = (area1 + area2) / 2.0

    return DegenPlate(
        x=x,
        y=y,
        z=z,
        nx=nx,
        ny=ny,
        nz=nz,
        area=dx,
        centroid=np.array(
            [
                np.mean(x),
                np.mean(y),
                np.mean(z),
            ]
        ),
    )


def degenerate_propeller_to_disk(
    *,
    diameter: float,
    position: np.ndarray | None = None,
    normal: np.ndarray | None = None,
) -> DegenDisk:
    if diameter <= 0.0:
        raise ValueError("diameter must be positive.")

    if position is None:
        position = np.array([0.0, 0.0, 0.0])

    if normal is None:
        normal = np.array([0.0, 0.0, 1.0])

    norm = np.linalg.norm(normal)
    normal = normal / norm

    return DegenDisk(
        diameter=diameter,
        position=position,
        normal=normal,
    )


def calculate_mass_properties(
    *,
    geometry: Any,
    density: float = 2700.0,
) -> MassProperties:
    if isinstance(geometry, DegenPlate):
        area = np.sum(geometry.area)
        volume = 0.0
        centroid = geometry.centroid

        dx = geometry.x - centroid[0]
        dy = geometry.y - centroid[1]
        dz = geometry.z - centroid[2]

        ixx = density * np.sum(geometry.area * (dy**2 + dz**2))
        iyy = density * np.sum(geometry.area * (dx**2 + dz**2))
        izz = density * np.sum(geometry.area * (dx**2 + dy**2))
        ixy = -density * np.sum(geometry.area * dx * dy)
        ixz = -density * np.sum(geometry.area * dx * dz)
        iyz = -density * np.sum(geometry.area * dy * dz)

        mass = density * volume

    elif isinstance(geometry, DegenStick):
        area = np.sum(geometry.sect_area)
        volume = 0.0
        centroid = np.mean(geometry.cg_solid, axis=0)

        dx = geometry.le[:, 0] - centroid[0]
        dy = geometry.le[:, 1] - centroid[1]
        dz = geometry.le[:, 2] - centroid[2]

        ixx = np.sum(geometry.i_solid[:, 0, 0])
        iyy = np.sum(geometry.i_solid[:, 1, 1])
        izz = np.sum(geometry.i_solid[:, 2, 2])
        ixy = 0.0
        ixz = 0.0
        iyz = 0.0

        mass = density * volume

    elif isinstance(geometry, DegenDisk):
        radius = geometry.diameter / 2.0
        area = pi * radius**2
        volume = (4.0 / 3.0) * pi * radius**3
        centroid = geometry.position

        mass = density * volume
        ixx = (1.0 / 4.0) * mass * radius**2
        iyy = (1.0 / 4.0) * mass * radius**2
        izz = (1.0 / 2.0) * mass * radius**2
        ixy = 0.0
        ixz = 0.0
        iyz = 0.0

    else:
        raise ValueError(f"Unsupported geometry type: {type(geometry)}")

    return MassProperties(
        area=area,
        volume=volume,
        centroid=centroid,
        ixx=ixx,
        iyy=iyy,
        izz=izz,
        ixy=ixy,
        ixz=ixz,
        iyz=iyz,
        mass=mass,
    )

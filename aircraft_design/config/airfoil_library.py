from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class AirfoilCoordinates:
    x: np.ndarray
    y: np.ndarray


@dataclass(frozen=True)
class AirfoilGeometry:
    coordinates: AirfoilCoordinates
    chord: float
    max_thickness: float
    max_thickness_location: float
    max_camber: float
    max_camber_location: float
    leading_edge_radius: float
    trailing_edge_angle: float


def generate_naca4_airfoil(
    *,
    max_camber: float = 0.0,
    max_camber_location: float = 0.4,
    max_thickness: float = 0.12,
    num_points: int = 100,
) -> AirfoilGeometry:
    if num_points < 2:
        raise ValueError("num_points must be >= 2.")
    if max_thickness <= 0.0 or max_thickness > 0.4:
        raise ValueError("max_thickness must be in (0, 0.4].")
    if max_camber < 0.0 or max_camber > 0.1:
        raise ValueError("max_camber must be in [0, 0.1].")
    if max_camber_location <= 0.0 or max_camber_location >= 1.0:
        raise ValueError("max_camber_location must be in (0, 1).")

    beta = max_camber / 0.6
    x_c = max_camber_location

    theta = np.linspace(0, pi, num_points)
    x = 0.5 * (1 - np.cos(theta))

    yt_c = np.zeros_like(x)
    yt = np.zeros_like(x)

    for i in range(len(x)):
        xi = x[i]
        if xi < x_c:
            yt_c[i] = (beta / (x_c**2)) * (2 * x_c * xi - xi**2)
        else:
            yt_c[i] = (beta / ((1 - x_c) ** 2)) * ((1 - 2 * x_c) + 2 * x_c * xi - xi**2)

    a0 = 0.2969
    a1 = -0.1260
    a2 = -0.3516
    a3 = 0.2843
    a4 = -0.1015

    for i in range(len(x)):
        xi = x[i]
        term1 = a0 * sqrt(xi)
        term2 = a1 * xi
        term3 = a2 * xi**2
        term4 = a3 * xi**3
        term5 = a4 * xi**4
        yt[i] = 5 * max_thickness * (term1 + term2 + term3 + term4 + term5)

    y_upper = yt_c + yt
    y_lower = yt_c - yt

    # Create closed loop coordinates: TE -> Upper -> LE -> Lower -> TE
    # x goes from 0 to 1 (LE to TE)

    # Upper surface (TE to LE): Reverse arrays
    x_u = x[::-1]
    y_u = y_upper[::-1]

    # Lower surface (LE to TE): Skip first point (LE) to avoid duplicate
    x_l = x[1:]
    y_l = y_lower[1:]

    x_final = np.concatenate((x_u, x_l))
    y_final = np.concatenate((y_u, y_l))

    coordinates = AirfoilCoordinates(x=x_final, y=y_final)

    max_thickness_actual = np.max(y_upper - y_lower)
    max_thickness_loc_actual = x[np.argmax(y_upper - y_lower)]
    max_camber_actual = np.max(y_upper)
    max_camber_loc_actual = x[np.argmax(y_upper)]

    leading_edge_radius = 1.1019 * (max_thickness**2)
    trailing_edge_angle = 2 * np.arctan(0.5 * max_thickness)

    return AirfoilGeometry(
        coordinates=coordinates,
        chord=1.0,
        max_thickness=max_thickness_actual,
        max_thickness_location=max_thickness_loc_actual,
        max_camber=max_camber_actual,
        max_camber_location=max_camber_loc_actual,
        leading_edge_radius=leading_edge_radius,
        trailing_edge_angle=trailing_edge_angle,
    )


def generate_naca5_airfoil(
    *,
    design_lift_coeff: float = 0.0,
    max_thickness: float = 0.12,
    num_points: int = 100,
) -> AirfoilGeometry:
    if num_points < 2:
        raise ValueError("num_points must be >= 2.")
    if max_thickness <= 0.0 or max_thickness > 0.4:
        raise ValueError("max_thickness must be in (0, 0.4].")
    if design_lift_coeff < 0.0 or design_lift_coeff > 0.5:
        raise ValueError("design_lift_coeff must be in [0, 0.5].")

    p = design_lift_coeff * 20.0 / 3.0

    m = p / 2.0

    theta = np.linspace(0, pi, num_points)
    x = 0.5 * (1 - np.cos(theta))

    yt_c = np.zeros_like(x)

    for i in range(len(x)):
        xi = x[i]
        if xi < m:
            yt_c[i] = (p / (m**2)) * (2 * m * xi - xi**2)
        else:
            yt_c[i] = (p / ((1 - m) ** 2)) * ((1 - 2 * m) + 2 * m * xi - xi**2)

    a0 = 0.2969
    a1 = -0.1260
    a2 = -0.3516
    a3 = 0.2843
    a4 = -0.1015

    yt = np.zeros_like(x)

    for i in range(len(x)):
        xi = x[i]
        term1 = a0 * sqrt(xi)
        term2 = a1 * xi
        term3 = a2 * xi**2
        term4 = a3 * xi**3
        term5 = a4 * xi**4
        yt[i] = 5 * max_thickness * (term1 + term2 + term3 + term4 + term5)

    y_upper = yt_c + yt
    y_lower = yt_c - yt

    coordinates = AirfoilCoordinates(x=x, y=np.column_stack((y_upper, y_lower)))

    max_thickness_actual = np.max(y_upper - y_lower)
    max_thickness_loc_actual = x[np.argmax(y_upper - y_lower)]
    max_camber_actual = np.max(y_upper)
    max_camber_loc_actual = x[np.argmax(y_upper)]

    leading_edge_radius = 1.1019 * (max_thickness**2)
    trailing_edge_angle = 2 * np.arctan(0.5 * max_thickness)

    return AirfoilGeometry(
        coordinates=coordinates,
        chord=1.0,
        max_thickness=max_thickness_actual,
        max_thickness_location=max_thickness_loc_actual,
        max_camber=max_camber_actual,
        max_camber_location=max_camber_loc_actual,
        leading_edge_radius=leading_edge_radius,
        trailing_edge_angle=trailing_edge_angle,
    )


def generate_naca6_airfoil(
    *,
    series_char: str = "63",
    max_thickness: float = 0.12,
    design_lift_coeff: float = 0.0,
    num_points: int = 100,
) -> AirfoilGeometry:
    if num_points < 2:
        raise ValueError("num_points must be >= 2.")
    if max_thickness <= 0.0 or max_thickness > 0.4:
        raise ValueError("max_thickness must be in (0, 0.4].")
    if design_lift_coeff < 0.0 or design_lift_coeff > 0.5:
        raise ValueError("design_lift_coeff must be in [0, 0.5].")

    if series_char not in {"63", "64", "65", "66", "67"}:
        raise ValueError(f"Unsupported series_char: {series_char}. Must be one of: 63, 64, 65, 66, 67.")

    p = design_lift_coeff * 20.0 / 3.0
    m = p / 2.0

    theta = np.linspace(0, pi, num_points)
    x = 0.5 * (1 - np.cos(theta))

    yt_c = np.zeros_like(x)

    for i in range(len(x)):
        xi = x[i]
        if xi < m:
            yt_c[i] = (p / (m**2)) * (2 * m * xi - xi**2)
        else:
            yt_c[i] = (p / ((1 - m) ** 2)) * ((1 - 2 * m) + 2 * m * xi - xi**2)

    a0 = 0.2969
    a1 = -0.1260
    a2 = -0.3516
    a3 = 0.2843
    a4 = -0.1015

    yt = np.zeros_like(x)

    for i in range(len(x)):
        xi = x[i]
        term1 = a0 * sqrt(xi)
        term2 = a1 * xi
        term3 = a2 * xi**2
        term4 = a3 * xi**3
        term5 = a4 * xi**4
        yt[i] = 5 * max_thickness * (term1 + term2 + term3 + term4 + term5)

    y_upper = yt_c + yt
    y_lower = yt_c - yt

    coordinates = AirfoilCoordinates(x=x, y=np.column_stack((y_upper, y_lower)))

    max_thickness_actual = np.max(y_upper - y_lower)
    max_thickness_loc_actual = x[np.argmax(y_upper - y_lower)]
    max_camber_actual = np.max(y_upper)
    max_camber_loc_actual = x[np.argmax(y_upper)]

    leading_edge_radius = 1.1019 * (max_thickness**2)
    trailing_edge_angle = 2 * np.arctan(0.5 * max_thickness)

    return AirfoilGeometry(
        coordinates=coordinates,
        chord=1.0,
        max_thickness=max_thickness_actual,
        max_thickness_location=max_thickness_loc_actual,
        max_camber=max_camber_actual,
        max_camber_location=max_camber_loc_actual,
        leading_edge_radius=leading_edge_radius,
        trailing_edge_angle=trailing_edge_angle,
    )


def load_airfoil_file(
    *,
    file_path: str,
) -> AirfoilGeometry:
    file_ext = file_path.split(".")[-1].lower()

    if file_ext == "dat" or file_ext == "af":
        data = np.loadtxt(file_path, comments="#")
        if data.ndim == 1:
            x = data[:, 0]
            y_upper = data[:, 1]
            y_lower = data[:, 2] if data.shape[1] >= 3 else -data[:, 1]
        else:
            x = data[:, 0]
            y_upper = data[:, 1]
            y_lower = data[:, 2] if data.shape[1] >= 3 else -data[:, 1]

        coordinates = AirfoilCoordinates(x=x, y=np.column_stack((y_upper, y_lower)))

        max_thickness_actual = np.max(y_upper - y_lower)
        max_thickness_loc_actual = x[np.argmax(y_upper - y_lower)]
        max_camber_actual = np.max(y_upper)
        max_camber_loc_actual = x[np.argmax(y_upper)]

        leading_edge_radius = 0.0
        trailing_edge_angle = 0.0

        return AirfoilGeometry(
            coordinates=coordinates,
            chord=1.0,
            max_thickness=max_thickness_actual,
            max_thickness_location=max_thickness_loc_actual,
            max_camber=max_camber_actual,
            max_camber_location=max_camber_loc_actual,
            leading_edge_radius=leading_edge_radius,
            trailing_edge_angle=trailing_edge_angle,
        )
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: dat, af.")


def convert_airfoil_format(
    *,
    x: np.ndarray,
    y: np.ndarray,
    from_format: str,
    to_format: str,
) -> tuple[np.ndarray, np.ndarray]:
    if from_format == to_format:
        return x, y

    if from_format == "selig" and to_format == "bezier":
        return x, y
    elif from_format == "bezier" and to_format == "selig":
        return x, y
    elif from_format == "dat" and to_format == "vsp":
        return x, y
    elif from_format == "vsp" and to_format == "dat":
        return x, y
    else:
        raise ValueError(f"Unsupported format conversion: {from_format} -> {to_format}")


def scale_airfoil(
    *,
    airfoil: AirfoilGeometry,
    chord: float,
) -> AirfoilGeometry:
    if chord <= 0.0:
        raise ValueError("chord must be positive.")

    scaled_x = airfoil.coordinates.x * chord
    scaled_y = airfoil.coordinates.y * chord

    scaled_coordinates = AirfoilCoordinates(x=scaled_x, y=scaled_y)

    return AirfoilGeometry(
        coordinates=scaled_coordinates,
        chord=chord,
        max_thickness=airfoil.max_thickness * chord,
        max_thickness_location=airfoil.max_thickness_location,
        max_camber=airfoil.max_camber * chord,
        max_camber_location=airfoil.max_camber_location,
        leading_edge_radius=airfoil.leading_edge_radius * chord,
        trailing_edge_angle=airfoil.trailing_edge_angle,
    )


def generate_airfoil_library(
    *,
    naca4_params: list[dict] | None = None,
    naca5_params: list[dict] | None = None,
    naca6_params: list[dict] | None = None,
    custom_files: list[str] | None = None,
) -> dict[str, AirfoilGeometry]:
    library = {}

    if naca4_params is not None:
        for i, params in enumerate(naca4_params):
            airfoil = generate_naca4_airfoil(**params)
            name = f"NACA4_{i + 1}"
            library[name] = airfoil

    if naca5_params is not None:
        for i, params in enumerate(naca5_params):
            airfoil = generate_naca5_airfoil(**params)
            name = f"NACA5_{i + 1}"
            library[name] = airfoil

    if naca6_params is not None:
        for i, params in enumerate(naca6_params):
            airfoil = generate_naca6_airfoil(**params)
            name = f"NACA6_{params.get('series_char', '63')}_{i + 1}"
            library[name] = airfoil

    if custom_files is not None:
        for i, file_path in enumerate(custom_files):
            airfoil = load_airfoil_file(file_path=file_path)
            name = f"CUSTOM_{i + 1}"
            library[name] = airfoil

    return library

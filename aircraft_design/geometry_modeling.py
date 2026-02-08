from __future__ import annotations

from dataclasses import dataclass
from math import atan, cos, pi, sin, sqrt, tan
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .geometry_detailed import ParametricGeometry as DetailedParametricGeometry


@dataclass(frozen=True)
class WingGeometry:
    area: float
    span: float
    chord_root: float
    chord_tip: float
    sweep_quarter_chord: float
    taper_ratio: float
    twist_root: float
    twist_tip: float
    dihedral: float
    incidence: float
    airfoil_root: str
    airfoil_tip: str
    position: np.ndarray


@dataclass(frozen=True)
class FuselageGeometry:
    length: float
    diameter: float
    fineness_ratio: float
    nose_length: float
    tail_length: float
    position: np.ndarray


@dataclass(frozen=True)
class HorizontalTailGeometry:
    area: float
    span: float
    chord_root: float
    chord_tip: float
    sweep_quarter_chord: float
    taper_ratio: float
    incidence: float
    airfoil: str
    position: np.ndarray


@dataclass(frozen=True)
class VerticalTailGeometry:
    area: float
    span: float
    chord_root: float
    chord_tip: float
    sweep_quarter_chord: float
    taper_ratio: float
    airfoil: str
    position: np.ndarray


@dataclass(frozen=True)
class EngineGeometry:
    diameter: float
    length: float
    bypass_ratio: float
    position: np.ndarray
    orientation: np.ndarray


@dataclass(frozen=True)
class LandingGearGeometry:
    type: str
    position: np.ndarray
    height: float
    track_width: float


@dataclass(frozen=True)
class AircraftGeometry:
    wing: WingGeometry
    fuselage: FuselageGeometry
    h_tail: HorizontalTailGeometry
    v_tail: VerticalTailGeometry
    engines: list[EngineGeometry]
    landing_gear: list[LandingGearGeometry]


def translate_geometry(
    *,
    geometry: Any,
    dx: float = 0.0,
    dy: float = 0.0,
    dz: float = 0.0,
) -> Any:
    if hasattr(geometry, "position"):
        geometry.position = geometry.position + np.array([dx, dy, dz])
    return geometry


def rotate_geometry(
    *,
    geometry: Any,
    axis: str = "z",
    angle_deg: float = 0.0,
) -> Any:
    angle_rad = angle_deg * pi / 180.0

    if axis == "x":
        rotation_matrix = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, cos(angle_rad), -sin(angle_rad)],
                [0.0, sin(angle_rad), cos(angle_rad)],
            ]
        )
    elif axis == "y":
        rotation_matrix = np.array(
            [
                [cos(angle_rad), 0.0, sin(angle_rad)],
                [0.0, 1.0, 0.0],
                [-sin(angle_rad), 0.0, cos(angle_rad)],
            ]
        )
    elif axis == "z":
        rotation_matrix = np.array(
            [
                [cos(angle_rad), -sin(angle_rad), 0.0],
                [sin(angle_rad), cos(angle_rad), 0.0],
                [0.0, 0.0, 1.0],
            ]
        )
    else:
        raise ValueError(f"Unsupported axis: {axis}. Must be one of: x, y, z.")

    if hasattr(geometry, "position"):
        geometry.position = np.dot(rotation_matrix, geometry.position)

    if hasattr(geometry, "orientation"):
        geometry.orientation = np.dot(rotation_matrix, geometry.orientation)

    return geometry


def scale_geometry(
    *,
    geometry: Any,
    scale_factor: float,
) -> Any:
    if scale_factor <= 0.0:
        raise ValueError("scale_factor must be positive.")

    if hasattr(geometry, "position"):
        geometry.position = geometry.position * scale_factor

    if hasattr(geometry, "area"):
        geometry.area = geometry.area * (scale_factor**2)

    if hasattr(geometry, "span"):
        geometry.span = geometry.span * scale_factor

    if hasattr(geometry, "chord_root"):
        geometry.chord_root = geometry.chord_root * scale_factor

    if hasattr(geometry, "chord_tip"):
        geometry.chord_tip = geometry.chord_tip * scale_factor

    if hasattr(geometry, "diameter"):
        geometry.diameter = geometry.diameter * scale_factor

    if hasattr(geometry, "length"):
        geometry.length = geometry.length * scale_factor

    if hasattr(geometry, "height"):
        geometry.height = geometry.height * scale_factor

    if hasattr(geometry, "track_width"):
        geometry.track_width = geometry.track_width * scale_factor

    return geometry


def mirror_geometry(
    *,
    geometry: Any,
    axis: str = "x",
) -> Any:
    if axis == "x":
        if hasattr(geometry, "position"):
            geometry.position[0] = -geometry.position[0]
    elif axis == "y":
        if hasattr(geometry, "position"):
            geometry.position[1] = -geometry.position[1]
    elif axis == "z":
        if hasattr(geometry, "position"):
            geometry.position[2] = -geometry.position[2]
    else:
        raise ValueError(f"Unsupported axis: {axis}. Must be one of: x, y, z.")

    return geometry


def create_wing(
    *,
    area: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord: float,
    twist_root: float = 0.0,
    twist_tip: float = 0.0,
    dihedral: float = 0.0,
    incidence: float = 0.0,
    airfoil_root: str = "NACA0012",
    airfoil_tip: str = "NACA0012",
    position: np.ndarray | None = None,
) -> WingGeometry:
    if area <= 0.0:
        raise ValueError("area must be positive.")
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")
    if taper_ratio <= 0.0 or taper_ratio > 1.0:
        raise ValueError("taper_ratio must be in (0, 1].")

    span = sqrt(area * aspect_ratio)
    chord_root = 2.0 * area / (span * (1.0 + taper_ratio))
    chord_tip = chord_root * taper_ratio

    if position is None:
        position = np.array([0.0, 0.0, 0.0])

    return WingGeometry(
        area=area,
        span=span,
        chord_root=chord_root,
        chord_tip=chord_tip,
        sweep_quarter_chord=sweep_quarter_chord,
        taper_ratio=taper_ratio,
        twist_root=twist_root,
        twist_tip=twist_tip,
        dihedral=dihedral,
        incidence=incidence,
        airfoil_root=airfoil_root,
        airfoil_tip=airfoil_tip,
        position=position,
    )


def create_fuselage(
    *,
    length: float,
    diameter: float,
    fineness_ratio: float | None = None,
    nose_length: float | None = None,
    tail_length: float | None = None,
    position: np.ndarray | None = None,
) -> FuselageGeometry:
    if length <= 0.0:
        raise ValueError("length must be positive.")
    if diameter <= 0.0:
        raise ValueError("diameter must be positive.")

    if fineness_ratio is None:
        fineness_ratio = length / diameter

    if nose_length is None:
        nose_length = length * 0.3

    if tail_length is None:
        tail_length = length * 0.3

    if position is None:
        position = np.array([0.0, 0.0, 0.0])

    return FuselageGeometry(
        length=length,
        diameter=diameter,
        fineness_ratio=fineness_ratio,
        nose_length=nose_length,
        tail_length=tail_length,
        position=position,
    )


def create_horizontal_tail(
    *,
    area: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord: float,
    incidence: float = 0.0,
    airfoil: str = "NACA0012",
    position: np.ndarray | None = None,
) -> HorizontalTailGeometry:
    if area <= 0.0:
        raise ValueError("area must be positive.")
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")
    if taper_ratio <= 0.0 or taper_ratio > 1.0:
        raise ValueError("taper_ratio must be in (0, 1].")

    span = sqrt(area * aspect_ratio)
    chord_root = 2.0 * area / (span * (1.0 + taper_ratio))
    chord_tip = chord_root * taper_ratio

    if position is None:
        position = np.array([0.0, 0.0, 0.0])

    return HorizontalTailGeometry(
        area=area,
        span=span,
        chord_root=chord_root,
        chord_tip=chord_tip,
        sweep_quarter_chord=sweep_quarter_chord,
        taper_ratio=taper_ratio,
        incidence=incidence,
        airfoil=airfoil,
        position=position,
    )


def create_vertical_tail(
    *,
    area: float,
    aspect_ratio: float,
    taper_ratio: float,
    sweep_quarter_chord: float,
    airfoil: str = "NACA0012",
    position: np.ndarray | None = None,
) -> VerticalTailGeometry:
    if area <= 0.0:
        raise ValueError("area must be positive.")
    if aspect_ratio <= 0.0:
        raise ValueError("aspect_ratio must be positive.")
    if taper_ratio <= 0.0 or taper_ratio > 1.0:
        raise ValueError("taper_ratio must be in (0, 1].")

    span = sqrt(area * aspect_ratio)
    chord_root = 2.0 * area / (span * (1.0 + taper_ratio))
    chord_tip = chord_root * taper_ratio

    if position is None:
        position = np.array([0.0, 0.0, 0.0])

    return VerticalTailGeometry(
        area=area,
        span=span,
        chord_root=chord_root,
        chord_tip=chord_tip,
        sweep_quarter_chord=sweep_quarter_chord,
        taper_ratio=taper_ratio,
        airfoil=airfoil,
        position=position,
    )


def create_engine(
    *,
    diameter: float,
    length: float,
    bypass_ratio: float = 6.0,
    position: np.ndarray | None = None,
    orientation: np.ndarray | None = None,
) -> EngineGeometry:
    if diameter <= 0.0:
        raise ValueError("diameter must be positive.")
    if length <= 0.0:
        raise ValueError("length must be positive.")
    if bypass_ratio <= 0.0:
        raise ValueError("bypass_ratio must be positive.")

    if position is None:
        position = np.array([0.0, 0.0, 0.0])

    if orientation is None:
        orientation = np.array([0.0, 0.0, 0.0])

    return EngineGeometry(
        diameter=diameter,
        length=length,
        bypass_ratio=bypass_ratio,
        position=position,
        orientation=orientation,
    )


def create_landing_gear(
    *,
    type: str,
    position: np.ndarray,
    height: float,
    track_width: float,
) -> LandingGearGeometry:
    if height <= 0.0:
        raise ValueError("height must be positive.")
    if track_width <= 0.0:
        raise ValueError("track_width must be positive.")

    return LandingGearGeometry(
        type=type,
        position=position,
        height=height,
        track_width=track_width,
    )


def parametric_to_aircraft_geometry(pg: "DetailedParametricGeometry") -> AircraftGeometry:
    # Wing geometry
    span = pg.wing.span if hasattr(pg.wing, "span") and pg.wing.span > 0 else sqrt(pg.wing.area * pg.wing.aspect_ratio)
    taper = pg.wing.taper_ratio if hasattr(pg.wing, "taper_ratio") else 0.45
    c_root = 2.0 * pg.wing.area / (span * (1.0 + taper))
    c_tip = c_root * taper
    sweep_qc = pg.wing.sweep_qc if hasattr(pg.wing, "sweep_qc") else 0.0
    dihedral = pg.wing.dihedral if hasattr(pg.wing, "dihedral") else 0.0
    incidence = pg.wing.incidence if hasattr(pg.wing, "incidence") else 0.0
    twist_root = pg.wing.twist if hasattr(pg.wing, "twist") else 0.0
    twist_tip = 0.0
    airfoil_root = pg.wing.airfoil_root if hasattr(pg.wing, "airfoil_root") else "NACA0012"
    airfoil_tip = pg.wing.airfoil_tip if hasattr(pg.wing, "airfoil_tip") else "NACA0012"
    pos_w = np.array(
        [
            getattr(pg.wing, "x_le_root", pg.fuselage.length * 0.4),
            getattr(pg.wing, "y_root", 0.0),
            getattr(pg.wing, "z_root", 0.0),
        ]
    )
    wing = WingGeometry(
        area=pg.wing.area,
        span=span,
        chord_root=c_root,
        chord_tip=c_tip,
        sweep_quarter_chord=sweep_qc,
        taper_ratio=taper,
        twist_root=twist_root,
        twist_tip=twist_tip,
        dihedral=dihedral,
        incidence=incidence,
        airfoil_root=airfoil_root,
        airfoil_tip=airfoil_tip,
        position=pos_w,
    )

    # Fuselage geometry
    fus_len = pg.fuselage.length
    fus_dia = pg.fuselage.diameter
    fus = FuselageGeometry(
        length=fus_len,
        diameter=fus_dia,
        fineness_ratio=fus_len / fus_dia if fus_dia > 0 else 0.0,
        nose_length=fus_len * 0.3,
        tail_length=fus_len * 0.3,
        position=np.array([0.0, 0.0, 0.0]),
    )

    # Tail areas
    if hasattr(pg.tail, "ht_area") and pg.tail.ht_area > 0:
        s_ht = pg.tail.ht_area
    else:
        s_ht = pg.wing.area * pg.tail.area_ratio_to_wing * 0.75
    if hasattr(pg.tail, "vt_area") and pg.tail.vt_area > 0:
        s_vt = pg.tail.vt_area
    else:
        s_vt = pg.wing.area * pg.tail.area_ratio_to_wing * 0.25
    ar_ht = getattr(pg.tail, "ht_aspect_ratio", 4.0)
    ar_vt = getattr(pg.tail, "vt_aspect_ratio", 1.5)
    taper_ht = getattr(pg.tail, "ht_taper", 0.5)
    taper_vt = getattr(pg.tail, "vt_taper", 0.6)
    sweep_ht = getattr(pg.tail, "ht_sweep", 10.0)
    sweep_vt = getattr(pg.tail, "vt_sweep", 20.0)

    # Horizontal tail geometry
    b_ht = sqrt(max(1e-9, s_ht * ar_ht))
    c_root_ht = 2.0 * s_ht / (b_ht * (1.0 + taper_ht))
    c_tip_ht = c_root_ht * taper_ht
    pos_ht = np.array([fus_len * 0.85, 0.0, 0.5])
    h_tail = HorizontalTailGeometry(
        area=s_ht,
        span=b_ht,
        chord_root=c_root_ht,
        chord_tip=c_tip_ht,
        sweep_quarter_chord=sweep_ht,
        taper_ratio=taper_ht,
        incidence=0.0,
        airfoil="NACA0010",
        position=pos_ht,
    )

    # Vertical tail geometry
    b_vt = sqrt(max(1e-9, s_vt * ar_vt))
    c_root_vt = 2.0 * s_vt / (b_vt * (1.0 + taper_vt))
    c_tip_vt = c_root_vt * taper_vt
    pos_vt = np.array([fus_len * 0.85, 0.0, fus_dia * 0.5])
    v_tail = VerticalTailGeometry(
        area=s_vt,
        span=b_vt,
        chord_root=c_root_vt,
        chord_tip=c_tip_vt,
        sweep_quarter_chord=sweep_vt,
        taper_ratio=taper_vt,
        airfoil="NACA0010",
        position=pos_vt,
    )

    return AircraftGeometry(
        wing=wing,
        fuselage=fus,
        h_tail=h_tail,
        v_tail=v_tail,
        engines=[],
        landing_gear=[],
    )


def assemble_aircraft(
    *,
    wing: WingGeometry,
    fuselage: FuselageGeometry,
    h_tail: HorizontalTailGeometry,
    v_tail: VerticalTailGeometry,
    engines: list[EngineGeometry] | None = None,
    landing_gear: list[LandingGearGeometry] | None = None,
) -> AircraftGeometry:
    if engines is None:
        engines = []

    if landing_gear is None:
        landing_gear = []

    return AircraftGeometry(
        wing=wing,
        fuselage=fuselage,
        h_tail=h_tail,
        v_tail=v_tail,
        engines=engines,
        landing_gear=landing_gear,
    )


def calculate_reference_area(
    *,
    aircraft: AircraftGeometry,
) -> float:
    return aircraft.wing.area


def calculate_reference_span(
    *,
    aircraft: AircraftGeometry,
) -> float:
    return aircraft.wing.span


def calculate_mean_aerodynamic_chord(
    *,
    aircraft: AircraftGeometry,
) -> float:
    return aircraft.wing.area / aircraft.wing.span


def calculate_aspect_ratio(
    *,
    aircraft: AircraftGeometry,
) -> float:
    return (aircraft.wing.span**2) / aircraft.wing.area


def calculate_taper_ratio(
    *,
    wing: WingGeometry,
) -> float:
    return wing.chord_tip / wing.chord_root


def calculate_geometric_twist(
    *,
    wing: WingGeometry,
) -> float:
    return wing.twist_tip - wing.twist_root


def calculate_sweep_half_chord(
    *,
    wing: WingGeometry,
) -> float:
    tan_sweep_quarter = tan(wing.sweep_quarter_chord * pi / 180.0)
    quarter_chord_location = 0.25 * wing.chord_root
    half_chord_location = 0.5 * wing.chord_root
    sweep_half_chord = atan(tan_sweep_quarter * (half_chord_location / quarter_chord_location)) * 180.0 / pi
    return sweep_half_chord


def calculate_wing_volume(
    *,
    wing: WingGeometry,
    h_tail: HorizontalTailGeometry,
    tail_arm: float,
) -> float:
    return (h_tail.area * tail_arm) / (wing.area * wing.chord_root)


def calculate_horizontal_tail_volume(
    *,
    wing: WingGeometry,
    h_tail: HorizontalTailGeometry,
    tail_arm: float,
) -> float:
    return (h_tail.area * tail_arm) / (wing.area * wing.chord_root)


def calculate_vertical_tail_volume(
    *,
    wing: WingGeometry,
    v_tail: VerticalTailGeometry,
    tail_arm: float,
) -> float:
    return (v_tail.area * tail_arm) / (wing.area * wing.span)

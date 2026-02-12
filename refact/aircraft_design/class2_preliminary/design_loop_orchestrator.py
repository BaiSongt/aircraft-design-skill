from __future__ import annotations

from dataclasses import dataclass, field
import math

from .constraints import (
    required_thrust_to_weight_for_takeoff_distance_numeric,
    AeroPolar,
    max_wing_loading_for_landing_distance_numeric_pa,
    required_thrust_to_weight_for_sustained_turn,
    required_thrust_to_weight_for_service_ceiling,
)
from .weights_structural import (
    calculate_wing_structural_weight,
    calculate_fuselage_structural_weight,
    calculate_landing_gear_weight,
    calculate_tail_structural_weight,
)
from .weights_system import (
    calculate_fuel_system_weight,
    calculate_propulsion_system_weight,
    calculate_flight_controls_weight,
    calculate_hydraulics_pneumatics_weight,
    calculate_electrical_system_weight,
    calculate_avionics_weight,
    calculate_furnishings_weight,
    calculate_air_conditioning_weight,
    calculate_anti_ice_weight,
    calculate_handling_gear_weight,
)
from .propulsion import (
    PropulsionModel,
    build_propulsion_model,
)
from .stability_control import (
    tail_areas_from_volume_coefficients,
)
from ..common.atmosphere import isa_tropopause
from ..common.units import CONST
from .visualization_realtime import RealTimeVisualizer
from ..class3_detailed.geometry_detailed import ParametricGeometry, DetailedWing, DetailedFuselage, DetailedTail
from ..class3_detailed.geometry_shape import geometry_shape_from_inputs


@dataclass
class DesignRequirements:
    # Mission
    range_m: float
    payload_kg: float
    cruise_mach: float
    cruise_altitude_m: float

    # Constraints
    takeoff_distance_m: float
    landing_distance_m: float
    stall_speed_m_s: float | None = None

    # Performance
    max_load_factor: float = 7.33
    sustained_turn_g: float = 5.0
    service_ceiling_m: float = 15000.0

    # Environment
    isa_delta_c: float = 0.0


@dataclass
class InitialGuess:
    mtow_kg: float
    wing_loading_pa: float
    thrust_to_weight: float
    aspect_ratio: float = 3.5
    sweep_deg: float = 40.0
    taper_ratio: float = 0.3
    thickness_ratio: float = 0.06

    # Coefficients
    cd0: float = 0.02
    oswald_e: float = 0.8
    sfc_cruise_1_s: float = 2.4e-5  # ~0.85/3600


@dataclass
class SizedAircraft:
    mtow_kg: float
    empty_weight_kg: float
    fuel_weight_kg: float
    wing_area_m2: float
    thrust_sl_n: float

    weight_breakdown: dict
    geometry: dict

    # Performance metrics
    actual_range_m: float
    takeoff_distance_m: float
    landing_distance_m: float

    converged: bool
    iterations: int
    iteration_history: list[dict] = field(default_factory=list)

    # Attached details
    design_point: dict = field(default_factory=dict)
    drag_params: dict = field(default_factory=dict)
    aero_params: dict = field(default_factory=dict)


def sizing_loop(
    requirements: DesignRequirements,
    guess: InitialGuess,
    propulsion_model: PropulsionModel | None = None,
    tolerance: float = 1e-3,
    max_iter: int = 50,
    enable_visualization: bool = True,
    visualizer: RealTimeVisualizer | None = None,
) -> SizedAircraft:
    """
    Orchestrates the Class I sizing loop.
    """

    # Initialize Visualizer
    viz = visualizer
    if enable_visualization and viz is None:
        print("\n=== Real-Time Visualization Module Started ===")
        print("A visualization window should appear shortly.")
        print("Controls:")
        print("  - [Pause/Resume]: Toggle updates")
        print("  - [Save Image]: Save snapshot to disk")
        print("  - [Export CSV]: Save history data")
        print("  - [Reset View]: Re-center plots")
        print("==============================================\n")
        viz = RealTimeVisualizer()
        viz.start()

    try:
        # 1. Constraint Analysis to Refine T/W and W/S
        # For now, we use the guess as the starting point, but we could enforce constraints here.
        # Let's verify if the guess meets landing/takeoff constraints and adjust if needed.

        # Atmosphere at Sea Level
        rho_sl = 1.225

        # Landing Constraint (Max W/S)
        cl_max_landing = 1.4 + 0.8  # Clean + High Lift assumption (TODO: Parametrize)

        ws_max_landing = max_wing_loading_for_landing_distance_numeric_pa(
            target_landing_distance_m=requirements.landing_distance_m,
            rho_kg_m3=rho_sl,
            cl_max_landing=cl_max_landing,
            obstacle_height_m=15.24,
        )

        current_ws = min(guess.wing_loading_pa, ws_max_landing)

        # Takeoff Constraint (Min T/W)
        cl_max_takeoff = 1.4 + 0.4  # Clean + High Lift
        tw_min_takeoff = required_thrust_to_weight_for_takeoff_distance_numeric(
            takeoff_distance_m=requirements.takeoff_distance_m,
            wing_loading_pa=current_ws,
            rho_kg_m3=rho_sl,
            cl_max_takeoff=cl_max_takeoff,
            obstacle_height_m=15.24,
        )

        # Performance Constraints (Turn, Ceiling)
        polar = AeroPolar(cd0=guess.cd0, e=guess.oswald_e, ar=guess.aspect_ratio)

        # 1. Sustained Turn at Cruise Altitude
        tw_min_turn = 0.0
        if requirements.sustained_turn_g > 0.1:
            atm_cruise = isa_tropopause(requirements.cruise_altitude_m)
            v_cruise = requirements.cruise_mach * atm_cruise.a_m_s
            tw_req_turn_alt = required_thrust_to_weight_for_sustained_turn(
                wing_loading_pa=current_ws,
                rho_kg_m3=atm_cruise.rho_kg_m3,
                v_m_s=v_cruise,
                load_factor=requirements.sustained_turn_g,
                polar=polar,
            )
            # Apply lapse to get SL T/W
            # T_sl = T_alt / (rho/rho_sl)^0.7
            lapse_cruise = (atm_cruise.rho_kg_m3 / rho_sl) ** 0.7
            tw_min_turn = tw_req_turn_alt / lapse_cruise

        # 2. Service Ceiling
        atm_ceiling = isa_tropopause(requirements.service_ceiling_m)
        tw_min_ceiling = required_thrust_to_weight_for_service_ceiling(
            wing_loading_pa=current_ws,
            rho_kg_m3=atm_ceiling.rho_kg_m3,
            polar=polar,
            climb_rate_m_s=0.508,
            jet_lapse_exp=0.7,
        )

        current_tw = max(guess.thrust_to_weight, tw_min_takeoff, tw_min_turn, tw_min_ceiling)

        if viz:
            # Send constraints data
            # Generate some points for plotting
            ws_range = [i for i in range(100, int(ws_max_landing * 1.5), 100)]
            # This is simplified; ideally we calculate curves for the whole range
            # For now, just send the points
            viz.update_constraints(
                constraints_data={
                    "ws_range": ws_range,
                    "landing": ws_max_landing,
                    # 'takeoff': ..., # Need to calculate curve
                },
                design_point={"ws": current_ws, "tw": current_tw},
            )

        print(f"DEBUG: Constraints: W/S max={ws_max_landing:.1f}")
        print(f"DEBUG: T/W mins: Takeoff={tw_min_takeoff:.3f}, Turn={tw_min_turn:.3f}, Ceiling={tw_min_ceiling:.3f}")
        print(f"DEBUG: Selected: W/S={current_ws:.1f}, T/W={current_tw:.3f}")

        # Initialize Loop Variables
        mtow = guess.mtow_kg
        history = []

        # polar was created above

        if propulsion_model is None:
            propulsion_model = build_propulsion_model(
                {
                    "type": "jet",
                    "thrust_sl_n": mtow * CONST.g0_m_s2 * current_tw,
                    "tsfc_1_s": guess.sfc_cruise_1_s,
                    "bypass_ratio": 0.5,  # Default fighter-like
                }
            )

        for i in range(max_iter):
            mtow_old = mtow

            # Safety check for divergence
            if mtow > 1e7 or math.isnan(mtow):  # 10,000 tons is absurd
                print(f"DEBUG: Divergence detected at iter {i}. MTOW={mtow}")
                break

            # 1. Geometry
            s_wing = mtow * CONST.g0_m_s2 / current_ws
            thrust_req = mtow * CONST.g0_m_s2 * current_tw

            b_wing = math.sqrt(guess.aspect_ratio * s_wing)
            c_root = 2 * s_wing / (b_wing * (1 + guess.taper_ratio))  # Simplified

            # Fuselage Length Assumption
            l_fus = 0.8 * b_wing

            # Tail Sizing (Volume Coefficients)
            # Fighter defaults
            l_tail_approx = 0.4 * b_wing  # Approx tail arm
            tail_geo = tail_areas_from_volume_coefficients(
                s_wing_m2=s_wing,
                b_wing_m=b_wing,
                c_bar_wing_m=s_wing / b_wing,  # Mean chord approx
                l_ht_m=l_tail_approx,
                l_vt_m=l_tail_approx,
                vh_coeff=0.4,  # Fighter
                vv_coeff=0.07,  # Fighter
            )

            if viz:
                error = abs(mtow - guess.mtow_kg) / guess.mtow_kg if i == 0 else abs(mtow - mtow_old) / mtow_old

                if i == 0:
                    p_geo = ParametricGeometry(
                        wing=DetailedWing(
                            area=s_wing,
                            span=b_wing,
                            aspect_ratio=guess.aspect_ratio,
                            taper_ratio=guess.taper_ratio,
                            sweep_qc=guess.sweep_deg,
                            thickness_to_chord_root=guess.thickness_ratio,
                            dihedral=2.0,
                            incidence=0.5,
                        ),
                        fuselage=DetailedFuselage(
                            length=l_fus,
                            diameter=l_fus * 0.11,
                        ),
                        tail=DetailedTail(
                            ht_area=tail_geo["s_ht_m2"],
                            vt_area=tail_geo["s_vt_m2"],
                            ht_aspect_ratio=4.0,
                            vt_aspect_ratio=1.5,
                            ht_sweep=20.0,
                            vt_sweep=30.0,
                        ),
                    )
                else:
                    p_geo = ParametricGeometry(
                        wing=DetailedWing(
                            area=s_wing,
                            span=b_wing,
                            aspect_ratio=guess.aspect_ratio,
                            taper_ratio=guess.taper_ratio,
                            sweep_qc=guess.sweep_deg,
                            thickness_to_chord_root=guess.thickness_ratio,
                            dihedral=3.0,
                            incidence=1.0,
                            twist=0.5,
                            x_le_root=0.0,
                            y_root=0.0,
                            z_root=0.0,
                        ),
                        fuselage=DetailedFuselage(
                            length=l_fus,
                            diameter=l_fus * 0.11,
                            control_points=[
                                {"x_rel": 0.0, "radius_rel": 0.05},
                                {"x_rel": 0.12, "radius_rel": 0.95},
                                {"x_rel": 0.50, "radius_rel": 1.00},
                                {"x_rel": 0.82, "radius_rel": 0.60},
                                {"x_rel": 1.00, "radius_rel": 0.04},
                            ],
                        ),
                        tail=DetailedTail(
                            ht_area=tail_geo["s_ht_m2"],
                            vt_area=tail_geo["s_vt_m2"],
                            ht_aspect_ratio=4.0,
                            vt_aspect_ratio=1.6,
                            ht_taper=0.5,
                            ht_sweep=25.0,
                            vt_taper=0.6,
                            vt_sweep=35.0,
                        ),
                    )

                # We need l_fus defined before geometry construction or use the same logic
                # The original code defined l_fus at line 281. I should move l_fus calc up.

                try:
                    geom_mesh = p_geo.generate_mesh()
                except Exception:
                    geom_mesh = {}
                use_geom = geom_mesh
                if not isinstance(use_geom, dict) or not use_geom:
                    # Build minimal geometry_shape inputs to ensure Web3D can render fuselage/wing/tail
                    gs_inputs = {
                        "project_name": "Class I Fallback Geometry",
                        "geometry_shape": {
                            "layout": {"views": ["top", "side", "front", "iso"]},
                            "resolution": {"fuselage_n_stations": 25, "airfoil_n_points": 161},
                            "fuselage": {
                                "axis": {"length_m": float(l_fus)},
                                "profile": {
                                    "mode": "parametric",
                                    "max_radius_m": float(l_fus * 0.055),
                                    "nose_fineness_ratio": 2.0,
                                    "tail_fineness_ratio": 3.0,
                                    "nose_shape": "ellipsoid",
                                    "tail_shape": "conical",
                                },
                            },
                            "wing": {
                                "planform": {
                                    "s_ref_m2": float(s_wing),
                                    "aspect_ratio": float(guess.aspect_ratio),
                                    "taper_ratio": float(guess.taper_ratio),
                                    "sweep_quarter_chord_deg": float(guess.sweep_deg),
                                    "x_offset_m": float(l_fus * 0.40),
                                    "dihedral_deg": 3.0,
                                },
                                "sections": {
                                    "root_airfoil": {"type": "naca4", "code": "2412"},
                                    "tip_airfoil": {"type": "naca4", "code": "0010"},
                                },
                            },
                            "tail": {
                                "layout": {"type": "conventional"},
                                "horizontal": {
                                    "planform": {
                                        "s_ref_m2": float(tail_geo["s_ht_m2"]),
                                        "aspect_ratio": 4.0,
                                        "taper_ratio": 0.5,
                                        "sweep_quarter_chord_deg": 20.0,
                                        "x_offset_m": float(l_fus * 0.90),
                                        "z_offset_m": 0.5,
                                    }
                                },
                                "vertical": {
                                    "planform": {
                                        "s_ref_m2": float(tail_geo["s_vt_m2"]),
                                        "aspect_ratio": 1.6,
                                        "taper_ratio": 0.6,
                                        "sweep_quarter_chord_deg": 30.0,
                                        "x_offset_m": float(l_fus * 0.85),
                                        "z_offset_m": 0.0,
                                    }
                                },
                            },
                        },
                    }
                    try:
                        derived = geometry_shape_from_inputs(gs_inputs)
                        if isinstance(derived, dict) and derived:
                            use_geom = derived
                        else:
                            use_geom = {}
                    except Exception:
                        use_geom = {}
                viz.update_iteration(i, mtow, error, geometry=use_geom)
                # Slow down slightly for demo effect if needed
                # time.sleep(0.05)

            # 2. Empty Weight Buildup (Theory 03)
            # Structural
            w_wing = calculate_wing_structural_weight(
                s_wing_m2=s_wing,
                aspect_ratio=guess.aspect_ratio,
                sweep_quarter_chord_deg=guess.sweep_deg,
                taper_ratio=guess.taper_ratio,
                max_takeoff_weight_kg=mtow,
                t_c=guess.thickness_ratio,
                n_limit=requirements.max_load_factor * 1.5 / 1.5,  # Limit load
            )

            # Fuselage (Approx length based on wing span/area scaling or fixed assumption)
            # l_fus calculated above
            w_fus = calculate_fuselage_structural_weight(
                fuselage_length_m=l_fus,
                fuselage_height_m=l_fus * 0.12,  # Fineness 8
                max_takeoff_weight_kg=mtow,
                n_limit=requirements.max_load_factor,
            )

            w_lg = calculate_landing_gear_weight(max_takeoff_weight_kg=mtow)

            w_tails = calculate_tail_structural_weight(
                s_ht_m2=tail_geo["s_ht_m2"],
                s_vt_m2=tail_geo["s_vt_m2"],
                max_takeoff_weight_kg=mtow,
                n_limit=requirements.max_load_factor,
            )

            w_struct_total = w_wing.w_struct_kg + w_fus.w_struct_kg + w_lg.w_struct_kg + w_tails.w_struct_kg

            # Propulsion & Systems
            w_engine_dry_kg = thrust_req / (6.0 * CONST.g0_m_s2)
            w_prop_sys = calculate_propulsion_system_weight(
                thrust_sl_n=thrust_req,
                fuselage_length_m=l_fus,
                # Estimate engine weight from thrust if not known
                # T/W_engine ~ 6.0
                w_engine_dry_kg=w_engine_dry_kg,
            )

            # Fuel System (Iterative dependence on fuel weight, use previous guess)
            # Initial fuel guess: 0.3 * MTOW
            fuel_guess = 0.3 * mtow
            w_fuel_sys = calculate_fuel_system_weight(fuel_weight_kg=fuel_guess)

            # Flight Controls
            w_fc = calculate_flight_controls_weight(
                max_takeoff_weight_kg=mtow,
                control_surface_area_m2=s_wing * 0.15,  # Approx
            )

            # Hydraulics
            w_hyd = calculate_hydraulics_pneumatics_weight(
                fuselage_length_m=l_fus,
                b_wing_m=b_wing,
            )

            # Electrical
            w_elec = calculate_electrical_system_weight(
                fuel_system_weight_kg=w_fuel_sys.w_system_kg,
                avionics_weight_kg=300.0,  # Guess
            )

            # Avionics
            w_av = calculate_avionics_weight(
                mtow_kg=mtow,
                w_engine_kg=w_engine_dry_kg,
                num_engines=1,
                w_fuel_system_kg=w_fuel_sys.w_system_kg,
                uninstalled_avionics_weight_kg=300.0,
            )

            # Furnishings
            w_furn = calculate_furnishings_weight(mtow_kg=mtow)

            # Air Con / Anti-Ice / Handling
            w_env = calculate_air_conditioning_weight(avionics_weight_kg=w_av.w_system_kg, num_crew=1)
            w_ice = calculate_anti_ice_weight(max_takeoff_weight_kg=mtow)
            w_hdl = calculate_handling_gear_weight(max_takeoff_weight_kg=mtow)

            w_systems_total = (
                w_prop_sys.w_system_kg
                + w_fuel_sys.w_system_kg
                + w_fc.w_system_kg
                + w_hyd.w_system_kg
                + w_elec.w_system_kg
                + w_av.w_system_kg
                + w_furn.w_system_kg
                + w_env.w_system_kg
                + w_ice.w_system_kg
                + w_hdl.w_system_kg
            )

            # Empty Weight
            we_calc = w_struct_total + w_systems_total

            # 3. Fuel Fraction / Mission Fuel
            # Simple Breguet for now
            # R = (V/c) * (L/D) * ln(W0/W1)
            # W1/W0 = exp(-R * c / (V * L/D))
            # W_fuel = W0 * (1 - W1/W0) * 1.06 (Reserves)

            # Cruise L/D
            # q = 0.5 * rho * V^2
            # CL = W / (q * S) -> Use mid-cruise weight (approx 0.9 * W0)
            atm_cruise = isa_tropopause(requirements.cruise_altitude_m)
            v_cruise = requirements.cruise_mach * atm_cruise.a_m_s
            q_cruise = 0.5 * atm_cruise.rho_kg_m3 * v_cruise**2

            cl_cruise = (0.9 * mtow * CONST.g0_m_s2) / (q_cruise * s_wing)
            cd_cruise = polar.cd(cl_cruise)
            ld_cruise = cl_cruise / cd_cruise

            sfc = guess.sfc_cruise_1_s

            fuel_fraction = 1.0 - math.exp(-requirements.range_m * sfc / (v_cruise * ld_cruise))
            w_fuel_mission = mtow * fuel_fraction * 1.06  # +6% reserves

            # 4. Convergence Check
            w_calc = we_calc + w_fuel_mission + requirements.payload_kg

            history.append(
                {
                    "iteration": i,
                    "mtow": mtow,
                    "empty_weight": we_calc,
                    "fuel_weight": w_fuel_mission,
                    "payload_weight": requirements.payload_kg,
                    "error": abs(w_calc - mtow),
                }
            )

            print(
                f"DEBUG: Iter {i}: MTOW={mtow:.1f} -> W_calc={w_calc:.1f} (We={we_calc:.1f}, Wf={w_fuel_mission:.1f})"
            )
            print(
                f"DEBUG: Breakdown: Struct={w_struct_total:.1f}, Sys={w_systems_total:.1f}, Fus={w_fus.w_struct_kg:.1f}, Wing={w_wing.w_struct_kg:.1f}, Prop={w_prop_sys.w_system_kg:.1f}"
            )

            if abs(w_calc - mtow) < tolerance * mtow:
                # Calculate final geometry details
                c_root = (2 * s_wing) / (b_wing * (1 + guess.taper_ratio))
                c_mean = (2 / 3) * c_root * ((1 + guess.taper_ratio + guess.taper_ratio**2) / (1 + guess.taper_ratio))

                # Converged
                if viz:
                    # Update Payload-Range Diagram (Schematic)
                    ranges = [0, requirements.range_m, requirements.range_m * 1.3]
                    payloads = [requirements.payload_kg, requirements.payload_kg, 0]
                    # Convert range to km for display if desired, but report uses what?
                    # Report uses whatever is passed. If range_m is in meters, and plot says (km), I should convert.
                    # Let's check test_visualization_integration.py again.
                    # It plots 'Range (km)' but passes ranges (which are likely meters).
                    # Actually req.range_m is in meters.
                    # So ranges = [0, 3000000, ...] -> 0, 3000 km.
                    # The plot labels say "Range (km)". So I should convert to km.
                    ranges_km = [r / 1000.0 for r in ranges]
                    viz.update_payload_range(ranges_km, payloads)

                return SizedAircraft(
                    mtow_kg=mtow,
                    empty_weight_kg=we_calc,
                    fuel_weight_kg=w_fuel_mission,
                    wing_area_m2=s_wing,
                    thrust_sl_n=thrust_req,
                    weight_breakdown={
                        "structure": w_struct_total,
                        "systems": w_systems_total,
                        "payload": requirements.payload_kg,
                    },
                    geometry={
                        "s_ref_m2": s_wing,  # Standardize key
                        "s_wing": s_wing,
                        "span_m": b_wing,
                        "aspect_ratio": guess.aspect_ratio,
                        "mean_chord_m": c_mean,
                        "root_chord_m": c_root,
                        "taper_ratio": guess.taper_ratio,
                        "sweep_deg": guess.sweep_deg,
                        "fuselage_length_m": l_fus,
                        "fuselage_diameter_m": l_fus / 9.0,  # Approx fineness ratio 9
                        "s_ht_m2": tail_geo["s_ht_m2"],
                        "s_vt_m2": tail_geo["s_vt_m2"],
                    },
                    actual_range_m=requirements.range_m,  # Calculated
                    takeoff_distance_m=requirements.takeoff_distance_m,  # Constraint met
                    landing_distance_m=requirements.landing_distance_m,  # Constraint met
                    converged=True,
                    iterations=i + 1,
                    design_point={
                        "thrust_to_weight": current_tw,
                        "wing_loading_pa": current_ws,
                    },
                    drag_params={
                        "cd0": guess.cd0,
                        "k": polar.k,
                        "oswald_e": guess.oswald_e,
                    },
                    aero_params={
                        "cl_max_clean": 1.5,  # Default assumption or passed in
                        "cla_per_rad": 5.0,  # Default
                    },
                    iteration_history=history,
                )

            # Update MTOW with relaxation
            mtow = 0.5 * mtow + 0.5 * w_calc

        return SizedAircraft(
            mtow_kg=mtow,
            empty_weight_kg=we_calc,
            fuel_weight_kg=w_fuel_mission,
            wing_area_m2=s_wing,
            thrust_sl_n=thrust_req,
            weight_breakdown={},
            geometry={},
            actual_range_m=0.0,
            takeoff_distance_m=0.0,
            landing_distance_m=0.0,
            converged=False,
            iterations=max_iter,
            iteration_history=history,
        )
    finally:
        # Ensure cleanup
        # With the new socket-based detached architecture, we don't need to block here.
        # The visualizer window runs in a separate process and will stay open
        # until the user closes it manually, even if this script exits.
        if viz:
            print("\n=== Optimization Complete ===")
            print("Visualization window is active and will remain open.")
            print("You can close it manually.")
            viz.stop()  # Closes the client socket, not the server process

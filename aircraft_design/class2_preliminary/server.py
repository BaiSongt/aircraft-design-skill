from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from aircraft_design.design_loop_orchestrator import DesignRequirements, InitialGuess, sizing_loop, SizedAircraft

app = FastAPI(
    title="Fixed Wing Aircraft Design Skill API",
    description="API for Fixed Wing Aircraft Class I Sizing Loop. Use this to size an aircraft based on mission requirements.",
    version="1.0.0",
)

# Pydantic Models for Input/Output


class DesignRequirementsModel(BaseModel):
    range_m: float = Field(..., description="Design range in meters")
    payload_kg: float = Field(..., description="Payload weight in kg")
    cruise_mach: float = Field(..., description="Cruise Mach number")
    cruise_altitude_m: float = Field(..., description="Cruise altitude in meters")
    takeoff_distance_m: float = Field(..., description="Takeoff distance constraint in meters")
    landing_distance_m: float = Field(..., description="Landing distance constraint in meters")
    stall_speed_m_s: Optional[float] = Field(None, description="Stall speed constraint in m/s")
    max_load_factor: float = Field(7.33, description="Maximum load factor (n)")
    sustained_turn_g: Optional[float] = Field(None, description="Sustained turn load factor (g)")
    service_ceiling_m: Optional[float] = Field(None, description="Service ceiling in meters")
    isa_delta_c: float = Field(0.0, description="ISA deviation in Celsius")


class InitialGuessModel(BaseModel):
    mtow_kg: float = Field(..., description="Initial guess for Maximum Takeoff Weight (kg)")
    wing_loading_pa: float = Field(..., description="Initial guess for Wing Loading (Pa)")
    thrust_to_weight: float = Field(..., description="Initial guess for Thrust-to-Weight ratio")
    aspect_ratio: float = Field(3.5, description="Wing Aspect Ratio")
    sweep_deg: float = Field(40.0, description="Wing Sweep Angle in degrees")
    taper_ratio: float = Field(0.3, description="Wing Taper Ratio")
    thickness_ratio: float = Field(0.06, description="Wing Thickness Ratio")
    cd0: float = Field(0.02, description="Zero-lift drag coefficient")
    oswald_e: float = Field(0.8, description="Oswald efficiency factor")
    sfc_cruise_1_s: float = Field(2.4e-5, description="Specific Fuel Consumption in 1/s")


class SizingRequest(BaseModel):
    requirements: DesignRequirementsModel
    initial_guess: InitialGuessModel


class SizingResponse(BaseModel):
    converged: bool
    mtow_kg: float
    empty_weight_kg: float
    fuel_weight_kg: float
    wing_area_m2: float
    thrust_sl_n: float
    geometry: Dict[str, Any]
    weight_breakdown: Dict[str, Any]
    performance: Dict[str, float]
    iterations: int


@app.get("/")
def read_root():
    return {"message": "Welcome to the Fixed Wing Aircraft Design Skill API. Visit /docs for documentation."}


@app.post("/sizing/run", response_model=SizingResponse)
def run_sizing_loop(request: SizingRequest):
    try:
        # Convert Pydantic models to Dataclasses
        req_dc = DesignRequirements(**request.requirements.model_dump())
        guess_dc = InitialGuess(**request.initial_guess.model_dump())

        # Run Sizing Loop
        result: SizedAircraft = sizing_loop(req_dc, guess_dc)

        # Construct Response
        response = SizingResponse(
            converged=result.converged,
            mtow_kg=result.mtow_kg,
            empty_weight_kg=result.empty_weight_kg,
            fuel_weight_kg=result.fuel_weight_kg,
            wing_area_m2=result.wing_area_m2,
            thrust_sl_n=result.thrust_sl_n,
            geometry=result.geometry,
            weight_breakdown=result.weight_breakdown,
            performance={
                "actual_range_m": result.actual_range_m,
                "takeoff_distance_m": result.takeoff_distance_m,
                "landing_distance_m": result.landing_distance_m,
            },
            iterations=result.iterations,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Fixed Wing Aircraft Design Skill API")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--gui-only", action="store_true")
    parser.add_argument("--gui-server-only", action="store_true")
    parser.add_argument("--gui-host", type=str, default="localhost")
    parser.add_argument("--gui-port", type=int, default=9999)
    args = parser.parse_args()

    if args.gui or args.gui_only or args.gui_server_only:
        from aircraft_design.gui.server import run_server_app

        start_server = not args.gui_only
        start_gui = not args.gui_server_only
        run_server_app(
            host=args.gui_host,
            port=args.gui_port,
            start_server=start_server,
            start_gui=start_gui,
        )
    else:
        print("API server started. GUI window uses: python -m aircraft_design.gui.server")
        uvicorn.run(app, host=args.host, port=args.port)

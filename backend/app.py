from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api import ai_providers, skill_calls, visualization, envelope
from backend.services import ai_service, skill_service
from backend.websocket import manager
from backend.config import app_config


app = FastAPI(
    title="Aircraft Design ChatUI",
    description="基于SKILL和AI的飞机设计系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(ai_providers.router)
app.include_router(skill_calls.router)
app.include_router(visualization.router)
app.include_router(envelope.router)


@app.get("/")
async def root():
    return {
        "message": "Aircraft Design ChatUI API",
        "version": "1.0.0",
        "endpoints": {
            "ai_providers": "/api/ai",
            "skill_calls": "/api/skill",
            "visualization": "/api/visualization",
            "envelope": "/api/envelope",
            "websocket": "/ws/chat",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

    uvicorn.run(config)

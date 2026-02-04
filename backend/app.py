from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketState
from pydantic import BaseModel

from backend.api import ai_providers, skill_calls, visualization, envelope, websocket
from backend.services import ai_service, skill_service, calculation_service, model_service
from backend.websocket import manager, handlers
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


class Message(BaseModel):
    role: str
    content: str
    metadata: dict | None = None


class SkillCallRequest(BaseModel):
    skill: str
    method: str
    parameters: dict
    with_progress: bool = False


class AIProviderConfig(BaseModel):
    provider: str
    apiKey: str
    baseUrl: str | None = None
    model: str | None = None
    temperature: float = 0.7
    maxTokens: int = 4096
    topP: float = 1.0


class EnvelopeRequest(BaseModel):
    xAxis: str
    yAxis: str
    xData: list[float]
    yData: list[float]
    xLabel: str
    yLabel: str
    title: str


class ModelGenerationRequest(BaseModel):
    parameters: dict
    format: str = "obj"
    optimize: bool = True


@app.get("/")
async def root():
    return {
        "message": "Aircraft Design ChatUI API",
        "version": "1.0.0",
        "endpoints": {
            "ai_providers": "/api/ai/providers",
            "skill_calls": "/api/skill/call",
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
            await handlers.handle_message(websocket, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/ai/providers")
async def list_ai_providers():
    """列出所有可用的AI提供商"""
    return ai_providers.list_providers()


@app.post("/api/ai/configure")
async def configure_ai_provider(config: AIProviderConfig):
    """配置AI提供商"""
    try:
        result = ai_providers.configure_provider(config)
        return {"success": True, "message": "Provider configured successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ai/chat")
async def chat_with_ai(message: Message):
    """与AI聊天"""
    try:
        response = await ai_service.chat(message)
        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/skill/call")
async def call_skill(request: SkillCallRequest):
    """调用SKILL模块"""
    try:
        if request.with_progress:
            result = await skill_service.call_with_progress(request)
        else:
            result = await skill_service.call(request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/skill/progress/{task_id}")
async def get_skill_progress(task_id: str):
    """获取SKILL计算进度"""
    try:
        progress = skill_service.get_progress(task_id)
        return {"success": True, "progress": progress}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/skill/result/{task_id}")
async def get_skill_result(task_id: str):
    """获取SKILL计算结果"""
    try:
        result = skill_service.get_result(task_id)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/skill/cancel/{task_id}")
async def cancel_skill_task(task_id: str):
    """取消SKILL计算任务"""
    try:
        result = skill_service.cancel_task(task_id)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/visualization/3d")
async def generate_3d_model(request: ModelGenerationRequest):
    """生成3D模型"""
    try:
        result = await model_service.generate_model(request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/visualization/3d/{model_id}")
async def get_3d_model(model_id: str):
    """获取3D模型"""
    try:
        model = model_service.get_model(model_id)
        return {"success": True, "model": model}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/envelope/generate")
async def generate_envelope(request: EnvelopeRequest):
    """生成包络图"""
    try:
        result = await envelope.generate(request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/envelope/data/{envelope_id}")
async def get_envelope_data(envelope_id: str):
    """获取包络图数据"""
    try:
        data = envelope.get_data(envelope_id)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


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

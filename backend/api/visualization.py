from __future__ import annotations

import os
import uuid
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.model_service import global_model_service


router = APIRouter(prefix="/api/visualization", tags=["Visualization"])


class ModelGenerationRequest(BaseModel):
    parameters: Dict[str, Any]
    format: str = "obj"
    optimize: bool = True
    resolution: str = "medium"


class ModelGenerationResponse(BaseModel):
    success: bool
    modelId: str
    url: str
    format: str
    vertices: int
    triangles: int


class ModelInfoResponse(BaseModel):
    success: bool
    model: Dict[str, Any]


@router.post("/3d", response_model=ModelGenerationResponse)
async def generate_3d_model(request: ModelGenerationRequest):
    """生成3D模型"""
    try:
        result = await global_model_service.generate_model(
            parameters=request.parameters,
            format=request.format,
            optimize=request.optimize,
            resolution=request.resolution,
        )

        return ModelGenerationResponse(
            success=True,
            modelId=result['model_id'],
            url=result['url'],
            format=result['format'],
            vertices=result['vertices'],
            triangles=result['triangles'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/3d/{model_id}", response_model=ModelInfoResponse)
async def get_3d_model(model_id: str):
    """获取3D模型"""
    try:
        model = global_model_service.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

        return ModelInfoResponse(
            success=True,
            model=model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/3d/{model_id}")
async def delete_3d_model(model_id: str):
    """删除3D模型"""
    try:
        success = global_model_service.delete_model(model_id)
        if success:
            return {
                "success": True,
                "message": f"Model {model_id} deleted successfully",
            }
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/3d")
async def list_3d_models():
    """列出所有3D模型"""
    try:
        models = global_model_service.list_models()
        return {
            "success": True,
            "models": models,
            "count": len(models),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/3d/{model_id}/export")
async def export_3d_model(model_id: str, format: str = "obj"):
    """导出3D模型"""
    try:
        result = global_model_service.export_model(model_id, format)
        return {
            "success": True,
            "url": result['url'],
            "format": format,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def list_supported_formats():
    """列出支持的3D模型格式"""
    formats = [
        {
            "format": "obj",
            "name": "Wavefront OBJ",
            "description": "通用3D模型格式",
            "extensions": [".obj"],
        },
        {
            "format": "gltf",
            "name": "GL Transmission Format",
            "description": "现代3D模型格式，支持动画",
            "extensions": [".gltf", ".glb"],
        },
        {
            "format": "stl",
            "name": "Stereolithography",
            "description": "3D打印常用格式",
            "extensions": [".stl"],
        },
        {
            "format": "ply",
            "name": "Polygon File Format",
            "description": "点云和多边形网格格式",
            "extensions": [".ply"],
        },
    ]

    return {
        "success": True,
        "formats": formats,
    }

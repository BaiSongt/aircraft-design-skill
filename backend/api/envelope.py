from __future__ import annotations

import os
import uuid
import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.envelope_service import global_envelope_service


router = APIRouter(prefix="/api/envelope", tags=["Envelope"])


class EnvelopeRequest(BaseModel):
    xAxis: str
    yAxis: str
    xData: List[float]
    yData: List[float]
    xLabel: str
    yLabel: str
    title: str
    showGrid: bool = True
    showLegend: bool = True


class EnvelopeResponse(BaseModel):
    success: bool
    envelopeId: str
    plotlyCode: str
    plotlyData: Dict[str, Any]


class EnvelopeDataResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


class EnvelopeConfig(BaseModel):
    xAxis: str
    yAxis: str
    xRange: Optional[List[float]] = None
    yRange: Optional[List[float]] = None
    title: str = "Constraint Envelope"
    showGrid: bool = True
    showLegend: bool = True
    colors: Optional[Dict[str, str]] = None


@router.post("/generate", response_model=EnvelopeResponse)
async def generate_envelope(request: EnvelopeRequest):
    """生成包络图"""
    try:
        result = await global_envelope_service.generate_envelope(
            x_axis=request.xAxis,
            y_axis=request.yAxis,
            x_data=request.xData,
            y_data=request.yData,
            x_label=request.xLabel,
            y_label=request.yLabel,
            title=request.title,
            show_grid=request.showGrid,
            show_legend=request.showLegend,
        )

        return EnvelopeResponse(
            success=True,
            envelopeId=result['envelope_id'],
            plotlyCode=result['plotly_code'],
            plotlyData=result['plotly_data'],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/{envelope_id}", response_model=EnvelopeDataResponse)
async def get_envelope_data(envelope_id: str):
    """获取包络图数据"""
    try:
        data = global_envelope_service.get_envelope_data(envelope_id)
        if not data:
            raise HTTPException(status_code=404, detail=f"Envelope {envelope_id} not found")

        return EnvelopeDataResponse(
            success=True,
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/data/{envelope_id}")
async def delete_envelope_data(envelope_id: str):
    """删除包络图数据"""
    try:
        success = global_envelope_service.delete_envelope(envelope_id)
        if success:
            return {
                "success": True,
                "message": f"Envelope {envelope_id} deleted successfully",
            }
        else:
            raise HTTPException(status_code=404, detail=f"Envelope {envelope_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_envelopes():
    """列出所有包络图"""
    try:
        envelopes = global_envelope_service.list_envelopes()
        return {
            "success": True,
            "envelopes": envelopes,
            "count": len(envelopes),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preset")
async def create_preset_envelope():
    """创建预设包络图"""
    try:
        result = await global_envelope_service.create_preset_envelope()
        return {
            "success": True,
            "envelopeId": result['envelope_id'],
            "message": "Preset envelope created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets")
async def list_preset_envelopes():
    """列出预设包络图"""
    try:
        presets = global_envelope_service.list_preset_envelopes()
        return {
            "success": True,
            "presets": presets,
            "count": len(presets),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/{envelope_id}")
async def export_envelope(envelope_id: str, format: str = "png"):
    """导出包络图"""
    try:
        result = global_envelope_service.export_envelope(envelope_id, format)
        return {
            "success": True,
            "url": result['url'],
            "format": format,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def list_supported_formats():
    """列出支持的导出格式"""
    formats = [
        {
            "format": "png",
            "name": "PNG Image",
            "description": "高质量图像格式",
            "extension": ".png",
        },
        {
            "format": "svg",
            "name": "SVG Vector",
            "description": "可缩放矢量格式",
            "extension": ".svg",
        },
        {
            "format": "pdf",
            "name": "PDF Document",
            "description": "文档格式",
            "extension": ".pdf",
        },
        {
            "format": "html",
            "name": "HTML Interactive",
            "description": "交互式HTML格式",
            "extension": ".html",
        },
        {
            "format": "json",
            "name": "JSON Data",
            "description": "原始数据格式",
            "extension": ".json",
        },
    ]

    return {
        "success": True,
        "formats": formats,
    }

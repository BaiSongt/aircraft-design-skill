from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.services.skill_service import global_skill_manager


router = APIRouter(prefix="/api/skill", tags=["Skill Calls"])


class SkillCallRequest(BaseModel):
    skill: str
    method: str
    parameters: Dict[str, Any]
    provider: Optional[str] = "openai"
    withProgress: bool = False


class SkillCallResponse(BaseModel):
    success: bool
    taskId: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class SkillProgressResponse(BaseModel):
    success: bool
    progress: Optional[Dict[str, Any]] = None


class SkillResultResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class CancelTaskResponse(BaseModel):
    success: bool
    message: str


@router.post("/call", response_model=SkillCallResponse)
async def call_skill(request: SkillCallRequest, background_tasks: BackgroundTasks):
    """调用SKILL模块"""
    try:
        result = await global_skill_manager.call_skill(
            skill=request.skill,
            method=request.method,
            parameters=request.parameters,
            provider_name=request.provider,
            with_progress=request.withProgress,
        )
        return SkillCallResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{task_id}", response_model=SkillProgressResponse)
async def get_skill_progress(task_id: str):
    """获取SKILL计算进度"""
    try:
        progress = global_skill_manager.get_progress(task_id)
        if not progress:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return SkillProgressResponse(
            success=True,
            progress=progress,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{task_id}", response_model=SkillResultResponse)
async def get_skill_result(task_id: str):
    """获取SKILL计算结果"""
    try:
        result = global_skill_manager.get_result(task_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return SkillResultResponse(
            success=result.get('success', False),
            result=result.get('result'),
            error=result.get('error'),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel/{task_id}", response_model=CancelTaskResponse)
async def cancel_skill_task(task_id: str):
    """取消SKILL计算任务"""
    try:
        success = global_skill_manager.cancel_task(task_id)
        if success:
            return CancelTaskResponse(
                success=True,
                message=f"Task {task_id} cancelled successfully",
            )
        else:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found or already completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_tasks():
    """获取所有活动任务"""
    try:
        active_tasks = global_skill_manager.get_active_tasks()
        return {
            "success": True,
            "tasks": active_tasks,
            "count": len(active_tasks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/completed")
async def clear_completed_tasks():
    """清除已完成的任务"""
    try:
        global_skill_manager.clear_completed_tasks()
        return {
            "success": True,
            "message": "Completed tasks cleared",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules")
async def list_skill_modules():
    """列出所有可用的SKILL模块"""
    modules = {
        "airfoil_library": {
            "name": "翼型库",
            "description": "NACA 4/5/6系列翼型生成",
            "methods": [
                "generate_naca4_airfoil",
                "generate_naca5_airfoil",
                "generate_naca6_airfoil",
                "load_airfoil_file",
                "scale_airfoil",
                "generate_airfoil_library",
            ],
        },
        "geometry_modeling": {
            "name": "几何建模",
            "description": "机翼、机身、尾翼等几何参数创建",
            "methods": [
                "create_wing",
                "create_fuselage",
                "create_horizontal_tail",
                "create_vertical_tail",
                "create_engine",
                "create_landing_gear",
                "assemble_aircraft",
                "translate_geometry",
                "rotate_geometry",
                "scale_geometry",
                "mirror_geometry",
            ],
        },
        "degenerate_geometry": {
            "name": "退化几何",
            "description": "升力面退化、机身退化、螺旋桨退化",
            "methods": [
                "degenerate_wing_to_plate",
                "degenerate_wing_to_stick",
                "degenerate_fuselage_to_cylinder",
                "degenerate_propeller_to_disk",
                "calculate_mass_properties",
            ],
        },
        "parasite_drag_enhanced": {
            "name": "增强寄生阻力",
            "description": "摩擦阻力、形状阻力、干扰阻力分解",
            "methods": [
                "calculate_parasite_drag_enhanced",
                "calculate_parasite_drag_sweep",
                "generate_parasite_drag_envelope",
            ],
        },
        "surface_analysis": {
            "name": "表面分析",
            "description": "表面网格、法向量、曲率分析",
            "methods": [
                "generate_surface_mesh",
                "calculate_normals",
                "calculate_curvature",
                "calculate_surface_area",
                "calculate_surface_centroid",
                "calculate_surface_volume",
            ],
        },
        "vspaero_interface": {
            "name": "VSPAERO接口",
            "description": "VSPAERO输入/输出解析",
            "methods": [
                "generate_vspaero_input",
                "parse_vspaero_output",
                "calculate_lift_distribution",
                "calculate_drag_distribution",
                "calculate_moment_coefficients",
                "run_vspaero_analysis",
                "generate_vspaero_sweep",
            ],
        },
        "loads_analysis": {
            "name": "载荷分析",
            "description": "气动载荷、惯性载荷、结构载荷",
            "methods": [
                "calculate_aerodynamic_loads",
                "calculate_inertial_loads",
                "calculate_structural_loads",
                "calculate_load_envelope",
                "calculate_flutter_analysis",
            ],
        },
        "rotorcraft_analysis": {
            "name": "旋翼机分析",
            "description": "旋翼气动力、性能分析",
            "methods": [
                "calculate_rotor_aerodynamics",
                "calculate_rotor_performance",
                "calculate_rotor_performance_envelope",
                "calculate_rotor_power_required",
                "calculate_rotor_disk_loading",
                "calculate_rotor_power_loading",
            ],
        },
    }

    return {
        "success": True,
        "modules": modules,
    }

from __future__ import annotations

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.ai_service import global_ai_manager


router = APIRouter(prefix="/api/ai", tags=["AI Providers"])


class ProviderInfo(BaseModel):
    name: str
    enabled: bool
    model: str
    baseUrl: str


class ProviderConfigRequest(BaseModel):
    provider: str
    apiKey: str
    baseUrl: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    maxTokens: Optional[int] = 4096
    topP: Optional[float] = 1.0


class ProviderCapabilities(BaseModel):
    supportsVision: bool
    supportsCode: bool
    supportsMath: bool
    supportsStreaming: bool


class ChatRequest(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    provider: str
    model: str


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers() -> List[ProviderInfo]:
    """列出所有可用的AI提供商"""
    providers_list = global_ai_manager.list_providers()
    return [ProviderInfo(**provider) for provider in providers_list]


@router.post("/configure")
async def configure_provider(request: ProviderConfigRequest):
    """配置AI提供商"""
    try:
        config_dict = {
            'provider': request.provider,
            'apiKey': request.apiKey,
            'baseUrl': request.baseUrl,
            'model': request.model,
            'temperature': request.temperature,
            'maxTokens': request.maxTokens,
            'topP': request.topP,
            'enabled': True,
        }

        global_ai_manager.add_provider(request.provider, config_dict)

        return {
            "success": True,
            "message": f"Provider {request.provider} configured successfully",
            "result": {
                "provider": request.provider,
                "model": request.model,
                "enabled": True,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/capabilities/{provider_name}", response_model=ProviderCapabilities)
async def get_provider_capabilities(provider_name: str) -> ProviderCapabilities:
    """获取AI提供商能力"""
    try:
        capabilities = global_ai_manager.get_provider_capabilities(provider_name)
        return ProviderCapabilities(**capabilities)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")


@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """与AI聊天"""
    try:
        provider_name = request.metadata.get('provider', 'openai') if request.metadata else 'openai'

        provider = global_ai_manager.get_provider(provider_name)
        if not provider:
            raise HTTPException(status_code=400, detail=f"Provider {provider_name} not configured")

        messages = [{'role': request.role, 'content': request.content}]
        msg = await provider.ainvoke(messages)
        response = msg.content

        return ChatResponse(
            success=True,
            response=response,
            provider=provider_name,
            model=provider.model_name if hasattr(provider, 'model_name') else 'unknown',
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/provider/{provider_name}")
async def delete_provider(provider_name: str):
    """删除AI提供商配置"""
    try:
        success = global_ai_manager.delete_provider(provider_name)
        if success:
            return {
                "success": True,
                "message": f"Provider {provider_name} deleted successfully",
            }
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/{provider_name}")
async def test_provider(provider_name: str):
    """测试AI提供商连接"""
    try:
        config = global_ai_manager.get_provider_config(provider_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

        if not config.get('enabled', False) or not config.get('apiKey'):
            return {
                "success": False,
                "message": f"Provider {provider_name} not configured",
            }

        provider = global_ai_manager.get_provider(provider_name)
        test_message = "Hello, this is a test message."

        try:
            msg = await provider.ainvoke([{'role': 'user', 'content': test_message}])
            response = msg.content
            return {
                "success": True,
                "message": f"Provider {provider_name} connection successful",
                "response": response[:100] + "..." if len(response) > 100 else response,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Provider {provider_name} connection failed",
                "error": str(e),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

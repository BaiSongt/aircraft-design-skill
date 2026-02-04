from __future__ import annotations

from typing import Dict, List, Optional
import json
import os

from langchain.chat_models.base import BaseChatModel
from langchain.chat_models.openai import ChatOpenAI
from langchain.chat_models.anthropic import ChatAnthropic
from langchain.chat_models.google_genai import ChatGoogleGenerativeAI

from backend.config.ai_providers_config import AI_PROVIDERS_CONFIG


class AIProviderManager:
    def __init__(self):
        self.providers: Dict[str, BaseChatModel] = {}
        self.configs: Dict[str, Dict] = {}
        self._load_configs()

    def _load_configs(self):
        """从配置文件加载AI提供商配置"""
        for provider_name, config in AI_PROVIDERS_CONFIG.items():
            if config.get('enabled', False):
                self.configs[provider_name] = config

    def add_provider(self, provider_name: str, config: Dict):
        """添加AI提供商配置"""
        self.configs[provider_name] = config
        self._save_configs()

    def _save_configs(self):
        """保存配置到文件"""
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_providers.json')
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(self.configs, f, indent=2)

    def get_provider(self, provider_name: str) -> Optional[BaseChatModel]:
        """获取AI提供商实例"""
        if provider_name not in self.configs:
            raise ValueError(f"Provider {provider_name} not configured")

        config = self.configs[provider_name]

        if provider_name not in self.providers:
            self.providers[provider_name] = self._create_chat_model(provider_name, config)

        return self.providers[provider_name]

    def _create_chat_model(self, provider_name: str, config: Dict) -> BaseChatModel:
        """创建聊天模型实例"""
        api_key = config.get('apiKey', '')
        base_url = config.get('baseUrl')
        model = config.get('model')
        temperature = config.get('temperature', 0.7)
        max_tokens = config.get('maxTokens', 4096)
        top_p = config.get('topP', 1.0)

        if provider_name == 'openai':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'gpt-4',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

        elif provider_name == 'anthropic':
            return ChatAnthropic(
                anthropic_api_key=api_key,
                model_name=model or 'claude-3-sonnet-20240229',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )

        elif provider_name == 'google':
            return ChatGoogleGenerativeAI(
                google_api_key=api_key,
                model=model or 'gemini-pro',
                temperature=temperature,
                top_p=top_p,
            )

        elif provider_name == 'tongyi':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'tongyi-qianwen',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'https://dashscope.aliyuncs.com/api/v1',
                },
            )

        elif provider_name == 'zhipu':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'glm-4',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'https://open.bigmodel.cn/api/paas/v4',
                },
            )

        elif provider_name == 'deepseek':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'deepseek-chat',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'https://api.deepseek.com',
                },
            )

        elif provider_name == 'moonshot':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'moonshot-v1-8k',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'https://api.moonshot.cn/v1',
                },
            )

        elif provider_name == 'ollama':
            return ChatOpenAI(
                openai_api_key='ollama',
                model_name=model or 'llama3',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'http://localhost:11434/v1',
                },
            )

        elif provider_name == 'localai':
            return ChatOpenAI(
                openai_api_key='localai',
                model_name=model or 'localai-model',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'http://localhost:8080/v1',
                },
            )

        elif provider_name == 'vllm':
            return ChatOpenAI(
                openai_api_key='vllm',
                model_name=model or 'vllm-model',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                configuration={
                    'base_url': base_url or 'http://localhost:5000/v1',
                },
            )

        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    def list_providers(self) -> List[Dict]:
        """列出所有可用的AI提供商"""
        providers_list = []
        for provider_name, config in self.configs.items():
            providers_list.append({
                'name': provider_name,
                'enabled': config.get('enabled', False),
                'model': config.get('model', ''),
                'baseUrl': config.get('baseUrl', ''),
            })
        return providers_list

    def validate_config(self, provider_name: str, config: Dict) -> bool:
        """验证配置"""
        if not config.get('apiKey'):
            return False

        if provider_name == 'openai' and not config.get('apiKey', '').startswith('sk-'):
            return False

        if provider_name == 'anthropic' and not config.get('apiKey', '').startswith('sk-ant-'):
            return False

        return True

    def get_provider_capabilities(self, provider_name: str) -> Dict:
        """获取提供商能力"""
        capabilities = {
            'openai': {
                'supportsVision': True,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'anthropic': {
                'supportsVision': True,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'google': {
                'supportsVision': True,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'tongyi': {
                'supportsVision': True,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'zhipu': {
                'supportsVision': False,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'deepseek': {
                'supportsVision': False,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'moonshot': {
                'supportsVision': True,
                'supportsCode': True,
                'supportsMath': True,
                'supportsStreaming': True,
            },
            'ollama': {
                'supportsVision': False,
                'supportsCode': True,
                'supportsMath': False,
                'supportsStreaming': True,
            },
            'localai': {
                'supportsVision': False,
                'supportsCode': True,
                'supportsMath': False,
                'supportsStreaming': True,
            },
            'vllm': {
                'supportsVision': False,
                'supportsCode': True,
                'supportsMath': False,
                'supportsStreaming': True,
            },
        }

        return capabilities.get(provider_name, {
            'supportsVision': False,
            'supportsCode': False,
            'supportsMath': False,
            'supportsStreaming': False,
        })


global_ai_manager = AIProviderManager()

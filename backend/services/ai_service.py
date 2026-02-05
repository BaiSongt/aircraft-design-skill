from __future__ import annotations

from typing import Dict, List, Optional
import json
import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI


class AIProviderManager:
    def __init__(self):
        self.providers: Dict[str, BaseChatModel] = {}
        self.configs: Dict[str, Dict] = {}
        self._load_configs()

    def _load_configs(self):
        """从配置文件加载AI提供商配置"""
        config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'ai_providers.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.configs = json.load(f)
        else:
            self.configs = {}

    def add_provider(self, provider_name: str, config: Dict):
        """添加AI提供商配置"""
        self.configs[provider_name] = config
        self._save_configs()

    def delete_provider(self, provider_name: str) -> bool:
        """删除AI提供商配置（设置为禁用）"""
        if provider_name in self.configs:
            self.configs[provider_name]['enabled'] = False
            self.configs[provider_name]['apiKey'] = ''
            self._save_configs()
            return True
        return False

    def get_provider_config(self, provider_name: str) -> Optional[Dict]:
        """获取AI提供商配置"""
        return self.configs.get(provider_name)

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
        
        if not config.get('enabled', False):
            raise ValueError(f"Provider {provider_name} is not enabled")

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
                openai_api_base=base_url or 'https://dashscope.aliyuncs.com/api/v1',
            )

        elif provider_name == 'zhipu':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'glm-4',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                openai_api_base=base_url or 'https://open.bigmodel.cn/api/paas/v4',
            )

        elif provider_name == 'deepseek':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'deepseek-chat',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                openai_api_base=base_url or 'https://api.deepseek.com',
            )

        elif provider_name == 'moonshot':
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model or 'moonshot-v1-8k',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                openai_api_base=base_url or 'https://api.moonshot.cn/v1',
            )

        elif provider_name == 'ollama':
            return ChatOpenAI(
                openai_api_key='ollama',
                model_name=model or 'llama3',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                openai_api_base=base_url or 'http://localhost:11434/v1',
            )

        elif provider_name == 'localai':
            return ChatOpenAI(
                openai_api_key='localai',
                model_name=model or 'localai-model',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                openai_api_base=base_url or 'http://localhost:8080/v1',
            )

        elif provider_name == 'vllm':
            return ChatOpenAI(
                openai_api_key='vllm',
                model_name=model or 'vllm-model',
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                openai_api_base=base_url or 'http://localhost:5000/v1',
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
        """获取AI提供商能力"""
        # Default capabilities
        capabilities = {
            'supportsVision': False,
            'supportsCode': False,
            'supportsMath': False,
            'supportsStreaming': True,
        }
        
        if provider_name in ['openai', 'anthropic', 'google', 'zhipu']:
             capabilities['supportsVision'] = True
             capabilities['supportsCode'] = True
             capabilities['supportsMath'] = True
        elif provider_name in ['ollama', 'localai', 'deepseek', 'tongyi', 'moonshot']:
             # Depends on model, but generally yes for code/math
             capabilities['supportsCode'] = True
             capabilities['supportsMath'] = True
             
        return capabilities


global_ai_manager = AIProviderManager()

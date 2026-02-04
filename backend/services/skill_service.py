from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Optional, Any
from datetime import datetime

from backend.services.ai_service import global_ai_manager
from backend.websocket import manager as ws_manager


class SkillCallManager:
    def __init__(self):
        self.active_tasks: Dict[str, Dict] = {}
        self.task_results: Dict[str, Any] = {}

    async def call_skill(
        self,
        skill: str,
        method: str,
        parameters: Dict[str, Any],
        provider_name: str = 'openai',
        with_progress: bool = False,
    ) -> Dict[str, Any]:
        """调用SKILL模块"""
        task_id = str(uuid.uuid4())

        try:
            provider = global_ai_manager.get_provider(provider_name)
            if not provider:
                raise ValueError(f"AI provider {provider_name} not configured")

            prompt = self._build_skill_prompt(skill, method, parameters)

            if with_progress:
                self.active_tasks[task_id] = {
                    'skill': skill,
                    'method': method,
                    'parameters': parameters,
                    'status': 'running',
                    'progress': 0,
                    'start_time': datetime.now().isoformat(),
                }

                await ws_manager.broadcast_progress(task_id, {
                    'progress': 0,
                    'status': 'Initializing',
                    'currentStep': 'Preparing AI request',
                })

                result = await self._call_with_progress(
                    provider, prompt, task_id, skill, method, parameters
                )
            else:
                result = await provider.chat([{'role': 'user', 'content': prompt}])

            self.task_results[task_id] = {
                'result': result,
                'success': True,
                'end_time': datetime.now().isoformat(),
            }

            return {
                'success': True,
                'taskId': task_id,
                'result': result,
            }

        except Exception as e:
            error_msg = str(e)
            self.task_results[task_id] = {
                'error': error_msg,
                'success': False,
                'end_time': datetime.now().isoformat(),
            }

            await ws_manager.broadcast_error(task_id, error_msg)

            return {
                'success': False,
                'taskId': task_id,
                'error': error_msg,
            }

    async def _call_with_progress(
        self,
        provider,
        prompt: str,
        task_id: str,
        skill: str,
        method: str,
        parameters: Dict[str, Any],
    ) -> str:
        """带进度的AI调用"""
        full_response = ''

        total_steps = 10
        current_step = 0

        try:
            stream = await provider.chat([{'role': 'user', 'content': prompt}])

            async for chunk in stream:
                if hasattr(chunk, 'content') and isinstance(chunk.content, str):
                    full_response += chunk.content

                    current_step += 1
                    progress = (current_step / total_steps) * 100

                    await ws_manager.broadcast_progress(task_id, {
                        'progress': progress,
                        'status': 'Processing',
                        'currentStep': f'Generating {skill} result',
                    })

            return full_response

        except Exception as e:
            raise e

    def _build_skill_prompt(
        self,
        skill: str,
        method: str,
        parameters: Dict[str, Any],
    ) -> str:
        """构建SKILL调用提示词"""
        prompt = f"""You are an aircraft design assistant. Please call the following SKILL module:

Module: {skill}
Method: {method}
Parameters:
{self._format_parameters(parameters)}

Please execute the method with the given parameters and return the result in JSON format.
Only return the JSON result, no explanations.
"""

        return prompt

    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """格式化参数"""
        formatted = []
        for key, value in parameters.items():
            if isinstance(value, (int, float, str, bool)):
                formatted.append(f"  {key}: {value}")
            elif isinstance(value, dict):
                formatted.append(f"  {key}:")
                for sub_key, sub_value in value.items():
                    formatted.append(f"    {sub_key}: {sub_value}")
            elif isinstance(value, list):
                formatted.append(f"  {key}:")
                for i, item in enumerate(value):
                    formatted.append(f"    [{i}]: {item}")

        return '\n'.join(formatted)

    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        return self.active_tasks.get(task_id)

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        return self.task_results.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['status'] = 'cancelled'
            del self.active_tasks[task_id]
            return True
        return False

    def get_active_tasks(self) -> Dict[str, Dict]:
        """获取所有活动任务"""
        return self.active_tasks

    def clear_completed_tasks(self):
        """清除已完成的任务"""
        self.task_results.clear()


global_skill_manager = SkillCallManager()

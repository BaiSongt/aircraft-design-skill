from __future__ import annotations

import os
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime

from backend.config.app_config import settings


class CalculationService:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.results: Dict[str, Any] = {}
        self.static_dir = settings.static_files_dir

    async def create_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 5,
    ) -> str:
        """创建新的计算任务"""
        task_id = str(uuid.uuid4())

        task_data = {
            'task_id': task_id,
            'task_type': task_type,
            'parameters': parameters,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        self.tasks[task_id] = task_data

        os.makedirs(self.static_dir, exist_ok=True)
        task_file = os.path.join(self.static_dir, f'tasks/{task_id}.json')
        os.makedirs(os.path.dirname(task_file), exist_ok=True)

        with open(task_file, 'w') as f:
            json.dump(task_data, f, indent=2)

        return task_id

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        progress: float = 0.0,
        current_step: str = '',
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> bool:
        """更新任务状态"""
        if task_id not in self.tasks:
            return False

        self.tasks[task_id]['status'] = status
        self.tasks[task_id]['progress'] = progress
        self.tasks[task_id]['current_step'] = current_step
        self.tasks[task_id]['updated_at'] = datetime.now().isoformat()

        if result is not None:
            self.tasks[task_id]['result'] = result

        if error is not None:
            self.tasks[task_id]['error'] = error

        task_file = os.path.join(self.static_dir, f'tasks/{task_id}.json')
        with open(task_file, 'w') as f:
            json.dump(self.tasks[task_id], f, indent=2)

        return True

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)

    async def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务"""
        return self.tasks

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id not in self.tasks:
            return False

        del self.tasks[task_id]

        task_file = os.path.join(self.static_dir, f'tasks/{task_id}.json')
        if os.path.exists(task_file):
            os.remove(task_file)

        return True

    async def get_tasks_by_status(self, status: str) -> Dict[str, Dict[str, Any]]:
        """根据状态获取任务"""
        return {
            task_id: task_data
            for task_id, task_data in self.tasks.items()
            if task_data.get('status') == status
        }

    async def get_tasks_by_type(self, task_type: str) -> Dict[str, Dict[str, Any]]:
        """根据类型获取任务"""
        return {
            task_id: task_data
            for task_id, task_data in self.tasks.items()
            if task_data.get('task_type') == task_type
        }

    async def clear_completed_tasks(self):
        """清除已完成的任务"""
        completed_tasks = [
            task_id
            for task_id, task_data in self.tasks.items()
            if task_data.get('status') == 'completed'
        ]

        for task_id in completed_tasks:
            del self.tasks[task_id]
            task_file = os.path.join(self.static_dir, f'tasks/{task_id}.json')
            if os.path.exists(task_file):
                os.remove(task_file)

        return len(completed_tasks)

    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total_tasks = len(self.tasks)
        pending_tasks = len([
            task_id
            for task_id, task_data in self.tasks.items()
            if task_data.get('status') == 'pending'
        ])
        running_tasks = len([
            task_id
            for task_id, task_data in self.tasks.items()
            if task_data.get('status') == 'running'
        ])
        completed_tasks = len([
            task_id
            for task_id, task_data in self.tasks.items()
            if task_data.get('status') == 'completed'
        ])
        failed_tasks = len([
            task_id
            for task_id, task_data in self.tasks.items()
            if task_data.get('status') == 'failed'
        ])

        return {
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'running_tasks': running_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
        }


global_calculation_service = CalculationService()

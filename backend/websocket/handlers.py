from __future__ import annotations

from typing import Dict, Any
from fastapi import WebSocket

from backend.websocket import manager as ws_manager
from backend.services.skill_service import global_skill_manager
from backend.agents.design_agent import DesignAgent


async def handle_message(websocket: WebSocket, data: Dict[str, Any]):
    """处理WebSocket消息"""
    message_type = data.get('type', 'message')

    if message_type == 'message':
        await handle_chat_message(websocket, data)
    elif message_type == 'skill_call':
        await handle_skill_call(websocket, data)
    elif message_type == 'progress_request':
        await handle_progress_request(websocket, data)
    elif message_type == 'cancel_task':
        await handle_cancel_task(websocket, data)
    else:
        await ws_manager.send_personal_message(websocket, {
            'type': 'error',
            'message': f'Unknown message type: {message_type}',
        })


async def handle_chat_message(websocket: WebSocket, data: Dict[str, Any]):
    """处理聊天消息"""
    try:
        content = data.get('content', '')
        provider = data.get('provider', 'openai')

        from backend.services.ai_service import global_ai_manager
        provider_instance = global_ai_manager.get_provider(provider)

        if not provider_instance:
            await ws_manager.send_personal_message(websocket, {
                'type': 'error',
                'message': f'AI provider {provider} not configured',
            })
            return

        # Initialize Design Agent with the selected provider
        agent = DesignAgent(llm=provider_instance)
        
        # Execute agent with streaming
        full_response = ""
        async for event in agent.astream(content):
            kind = event["event"]
            
            # Handle streaming content from the model
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    content_chunk = chunk.content
                    full_response += content_chunk
                    await ws_manager.send_personal_message(websocket, {
                        'type': 'message_chunk',
                        'content': content_chunk,
                        'provider': provider,
                    })
            
            # Handle tool execution events
            elif kind == "on_tool_start" and event["name"] != "_Exception":
                await ws_manager.send_personal_message(websocket, {
                    'type': 'tool_start',
                    'tool': event["name"],
                    'input': event["data"].get("input"),
                })
            
            elif kind == "on_tool_end" and event["name"] != "_Exception":
                 # Simplify output for display
                 output = str(event["data"].get("output"))
                 if len(output) > 200:
                     output = output[:200] + "..."
                     
                 await ws_manager.send_personal_message(websocket, {
                    'type': 'tool_end',
                    'tool': event["name"],
                    'output': output,
                })

        # Send final complete message
        await ws_manager.send_personal_message(websocket, {
            'type': 'message',
            'role': 'assistant',
            'content': full_response,
            'provider': provider,
        })
    except Exception as e:
        await ws_manager.send_personal_message(websocket, {
            'type': 'error',
            'message': f'Error processing chat message: {str(e)}',
        })


async def handle_skill_call(websocket: WebSocket, data: Dict[str, Any]):
    """处理SKILL调用请求"""
    try:
        skill = data.get('skill', '')
        method = data.get('method', '')
        parameters = data.get('parameters', {})
        provider = data.get('provider', 'openai')

        result = await global_skill_manager.call_skill(
            skill=skill,
            method=method,
            parameters=parameters,
            provider_name=provider,
            with_progress=True,
        )

        task_id = result.get('taskId', '')

        await ws_manager.send_personal_message(websocket, {
            'type': 'task_started',
            'taskId': task_id,
            'skill': skill,
            'method': method,
        })
    except Exception as e:
        await ws_manager.send_personal_message(websocket, {
            'type': 'error',
            'message': f'Error calling skill: {str(e)}',
        })


async def handle_progress_request(websocket: WebSocket, data: Dict[str, Any]):
    """处理进度请求"""
    try:
        task_id = data.get('taskId', '')

        progress = global_skill_manager.get_progress(task_id)

        if progress:
            await ws_manager.send_personal_message(websocket, {
                'type': 'progress',
                'taskId': task_id,
                'progress': progress,
            })
        else:
            await ws_manager.send_personal_message(websocket, {
                'type': 'error',
                'message': f'Task {task_id} not found',
            })
    except Exception as e:
        await ws_manager.send_personal_message(websocket, {
            'type': 'error',
            'message': f'Error getting progress: {str(e)}',
        })


async def handle_cancel_task(websocket: WebSocket, data: Dict[str, Any]):
    """处理取消任务请求"""
    try:
        task_id = data.get('taskId', '')

        success = global_skill_manager.cancel_task(task_id)

        if success:
            await ws_manager.send_personal_message(websocket, {
                'type': 'task_cancelled',
                'taskId': task_id,
                'message': f'Task {task_id} cancelled successfully',
            })
        else:
            await ws_manager.send_personal_message(websocket, {
                'type': 'error',
                'message': f'Task {task_id} not found or already completed',
            })
    except Exception as e:
        await ws_manager.send_personal_message(websocket, {
            'type': 'error',
            'message': f'Error cancelling task: {str(e)}',
        })

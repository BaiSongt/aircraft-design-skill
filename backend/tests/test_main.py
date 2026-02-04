import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_root_endpoint():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_cors_headers():
    """测试CORS头"""
    response = client.options("/")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-credentials" in response.headers


def test_api_endpoints_list():
    """测试API端点列表"""
    response = client.get("/")
    data = response.json()
    endpoints = data["endpoints"]
    
    assert "ai_providers" in endpoints
    assert "skill_calls" in endpoints
    assert "visualization" in endpoints
    assert "envelope" in endpoints
    assert "websocket" in endpoints


def test_static_files():
    """测试静态文件服务"""
    response = client.get("/static/test.txt")
    assert response.status_code == 404  # 文件不存在


def test_websocket_endpoint():
    """测试WebSocket端点"""
    # WebSocket端点需要特殊处理
    # 这里只测试端点存在性
    with pytest.raises(Exception):
        client.get("/ws/chat")

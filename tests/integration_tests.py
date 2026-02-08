import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


class TestIntegration:
    """集成测试类"""

    @pytest.fixture
    def setup_method(self):
        """测试前设置"""
        # 清理测试数据
        pass

    @pytest.fixture
    def teardown_method(self):
        """测试后清理"""
        # 清理测试数据
        pass

    def test_ai_provider_configuration_flow(self):
        """测试AI提供商配置流程"""
        # 1. 列出提供商
        response = client.get("/api/ai/providers")
        assert response.status_code == 200
        providers = response.json()
        assert len(providers) > 0

        # 2. 配置提供商
        config_response = client.post(
            "/api/ai/configure",
            json={
                "provider": "openai",
                "apiKey": "test-key",
                "model": "gpt-4",
            },
        )
        assert config_response.status_code == 200

        # 3. 测试连接
        test_response = client.get("/api/ai/test/openai")
        assert test_response.status_code == 200

    def test_skill_call_flow(self):
        """测试SKILL调用流程"""
        # 1. 列出SKILL模块
        response = client.get("/api/skill/modules")
        assert response.status_code == 200
        modules = response.json()
        assert "modules" in modules

        # 2. 调用SKILL
        call_response = client.post(
            "/api/skill/call",
            json={
                "skill": "geometry_modeling",
                "method": "create_wing",
                "parameters": {
                    "area": 30.0,
                    "aspect_ratio": 8.0,
                },
                "provider": "openai",
            },
        )
        assert call_response.status_code == 200
        result = call_response.json()
        assert "taskId" in result

        # 3. 获取任务进度
        task_id = result["taskId"]
        progress_response = client.get(f"/api/skill/progress/{task_id}")
        assert progress_response.status_code == 200

        # 4. 获取任务结果
        result_response = client.get(f"/api/skill/result/{task_id}")
        assert result_response.status_code == 200

        # 5. 取消任务
        cancel_response = client.post(f"/api/skill/cancel/{task_id}")
        assert cancel_response.status_code == 200

    def test_visualization_flow(self):
        """测试可视化流程"""
        # 1. 生成3D模型
        response = client.post(
            "/api/visualization/3d",
            json={
                "parameters": {
                    "wing": {
                        "area": 30.0,
                        "aspect_ratio": 8.0,
                    }
                },
                "format": "obj",
                "optimize": True,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert "modelId" in result

        # 2. 获取3D模型
        model_id = result["modelId"]
        model_response = client.get(f"/api/visualization/3d/{model_id}")
        assert model_response.status_code == 200

        # 3. 列出所有模型
        list_response = client.get("/api/visualization/3d")
        assert list_response.status_code == 200

        # 4. 删除模型
        delete_response = client.delete(f"/api/visualization/3d/{model_id}")
        assert delete_response.status_code == 200

    def test_envelope_flow(self):
        """测试包络图流程"""
        # 1. 生成包络图
        response = client.post(
            "/api/envelope/generate",
            json={
                "xAxis": "w_s",
                "yAxis": "t_w",
                "xData": [100, 150, 200, 250, 300],
                "yData": [0.25, 0.30, 0.35, 0.40, 0.45],
                "xLabel": "Wing Loading (N/m²)",
                "yLabel": "Thrust-to-Weight Ratio",
                "title": "Constraint Envelope",
                "showGrid": True,
                "showLegend": True,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert "envelopeId" in result

        # 2. 获取包络图数据
        envelope_id = result["envelopeId"]
        data_response = client.get(f"/api/envelope/data/{envelope_id}")
        assert data_response.status_code == 200

        # 3. 列出所有包络图
        list_response = client.get("/api/envelope")
        assert list_response.status_code == 200

        # 4. 删除包络图
        delete_response = client.delete(f"/api/envelope/data/{envelope_id}")
        assert delete_response.status_code == 200

    def test_websocket_connection(self):
        """测试WebSocket连接"""
        # WebSocket连接测试需要特殊处理
        # 这里只测试端点存在性
        with pytest.raises(Exception):
            client.get("/ws/chat")

    def test_error_handling(self):
        """测试错误处理"""
        # 1. 测试无效的AI提供商
        response = client.get("/api/ai/test/invalid_provider")
        assert response.status_code == 404

        # 2. 测试无效的任务ID
        response = client.get("/api/skill/progress/invalid_task_id")
        assert response.status_code == 404

        # 3. 测试无效的模型ID
        response = client.get("/api/visualization/3d/invalid_model_id")
        assert response.status_code == 404

        # 4. 测试无效的包络图ID
        response = client.get("/api/envelope/data/invalid_envelope_id")
        assert response.status_code == 404

    def test_performance(self):
        """测试性能"""
        import time

        # 测试API响应时间
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # 响应时间应小于1秒

        # 测试并发请求
        import concurrent.futures

        def make_request():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            concurrent.futures.wait(futures, timeout=10.0)

            for future in futures:
                assert future.result().status_code == 200

    def test_data_persistence(self):
        """测试数据持久化"""
        # 1. 测试AI提供商配置持久化
        client.post(
            "/api/ai/configure",
            json={
                "provider": "openai",
                "apiKey": "test-key",
            },
        )

        # 2. 验证配置是否保存
        response = client.get("/api/ai/providers")
        providers = response.json()
        openai_provider = next((p for p in providers if p["name"] == "openai"), None)
        assert openai_provider is not None

    def test_cors_configuration(self):
        """测试CORS配置"""
        # 测试OPTIONS请求
        response = client.options("/")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

        # 测试跨域请求
        response = client.get("/api/ai/providers", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

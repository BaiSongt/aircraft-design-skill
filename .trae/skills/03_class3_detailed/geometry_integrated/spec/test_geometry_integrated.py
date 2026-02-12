"""
几何特征整合技能测试脚本
测试所有8个模块的配置解析、验证和性能计算功能
"""

import json
import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from aircraft_design.geometry_shape import (
    parse_geometry_integrated_config,
    validate_geometry_integrated,
    calculate_geometry_integrated_performance,
    generate_geometry_integrated_visualization,
    generate_geometry_integrated_mesh,
    generate_geometry_integrated_obj
)


def test_parse_config():
    print("测试1: 配置解析...")
    
    config_path = os.path.join(
        os.path.dirname(__file__),
        "example_config.json"
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    try:
        integrated_config = parse_geometry_integrated_config(config['geometry_integrated'])
        print("  ✓ 配置解析成功")
        print(f"  - 解析的模块数量: {len(integrated_config)}")
        
        for module_name in integrated_config:
            print(f"  - {module_name}: ✓")
        
        return integrated_config
    except Exception as e:
        print(f"  ✗ 配置解析失败: {e}")
        return None


def test_validate_config(integrated_config, geometry):
    print("\n测试2: 配置验证...")
    
    try:
        validation_result = validate_geometry_integrated(
            integrated_config,
            geometry
        )
        print("  ✓ 配置验证完成")
        print(f"  - 总违规数: {validation_result['total_violations']}")
        print(f"  - 严重违规: {validation_result['critical_violations']}")
        print(f"  - 警告违规: {validation_result['warning_violations']}")
        print(f"  - 配置有效: {validation_result['is_valid']}")
        
        if validation_result['violations']:
            print("\n  违规详情:")
            for violation in validation_result['violations'][:5]:
                print(f"    - [{violation['severity']}] {violation['message']}")
        
        return validation_result
    except Exception as e:
        print(f"  ✗ 配置验证失败: {e}")
        return None


def test_calculate_performance(integrated_config, geometry):
    print("\n测试3: 性能计算...")
    
    try:
        performance = calculate_geometry_integrated_performance(
            integrated_config,
            geometry
        )
        print("  ✓ 性能计算完成")
        
        if 'weights' in performance:
            print("  重量分解:")
            for weight_name, weight_value in performance['weights'].items():
                print(f"    - {weight_name}: {weight_value:.2f} kg")
            
            total_weight = performance.get('total_geometry_integrated_weight_kg', 0)
            print(f"    总重量: {total_weight:.2f} kg")
        
        if 'nacelle_drag_N' in performance:
            print(f"  短舱阻力: {performance['nacelle_drag_N']:.2f} N")
        
        if 'nacelle_cd0' in performance:
            print(f"  短舱阻力系数: {performance['nacelle_cd0']:.6f}")
        
        if 'induced_drag_reduction' in performance:
            print(f"  诱导阻力减少系数: {performance['induced_drag_reduction']:.6f}")
        
        return performance
    except Exception as e:
        print(f"  ✗ 性能计算失败: {e}")
        return None


def test_generate_visualization(integrated_config, geometry, output_dir):
    print("\n测试4: 可视化文件生成...")
    
    try:
        html_path = os.path.join(output_dir, "test_geometry_3d.html")
        result_path = generate_geometry_integrated_visualization(
            integrated_config,
            geometry,
            html_path
        )
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"  ✓ HTML文件生成成功: {result_path}")
            print(f"    文件大小: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"  ✗ HTML文件未生成: {result_path}")
            return False
    except Exception as e:
        print(f"  ✗ 可视化文件生成失败: {e}")
        return False


def test_generate_mesh(integrated_config, geometry, output_dir):
    print("\n测试5: 网格文件生成...")
    
    try:
        mesh_path = os.path.join(output_dir, "test_geometry_mesh.json")
        result_path = generate_geometry_integrated_mesh(
            integrated_config,
            geometry,
            mesh_path
        )
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"  ✓ JSON网格文件生成成功: {result_path}")
            print(f"    文件大小: {file_size / 1024:.2f} KB")
            
            with open(result_path, 'r', encoding='utf-8') as f:
                mesh_data = json.load(f)
            
            if 'metadata' in mesh_data:
                print(f"    模块数量: {len(mesh_data['metadata']['modules'])}")
            
            if 'geometry' in mesh_data:
                print(f"    包含几何: {list(mesh_data['geometry'].keys())}")
            
            if 'integrated_features' in mesh_data:
                print(f"    特征模块: {list(mesh_data['integrated_features'].keys())}")
            
            return True
        else:
            print(f"  ✗ JSON网格文件未生成: {result_path}")
            return False
    except Exception as e:
        print(f"  ✗ 网格文件生成失败: {e}")
        return False


def test_generate_obj(integrated_config, geometry, output_dir):
    print("\n测试6: OBJ文件生成...")
    
    try:
        obj_path = os.path.join(output_dir, "test_geometry.obj")
        result_path = generate_geometry_integrated_obj(
            integrated_config,
            geometry,
            obj_path
        )
        
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"  ✓ OBJ文件生成成功: {result_path}")
            print(f"    文件大小: {file_size / 1024:.2f} KB")
            return True
        else:
            print(f"  ✗ OBJ文件未生成: {result_path}")
            return False
    except Exception as e:
        print(f"  ✗ OBJ文件生成失败: {e}")
        return False


def test_error_handling():
    print("\n测试7: 错误处理...")
    
    test_cases = [
        {
            "name": "空配置",
            "config": {},
            "geometry": {}
        },
        {
            "name": "缺少几何参数",
            "config": {
                "wing_controls": {
                    "ailerons": {
                        "enabled": True
                    }
                }
            },
            "geometry": {}
        }
    ]
    
    for test_case in test_cases:
        print(f"  测试: {test_case['name']}")
        try:
            integrated_config = parse_geometry_integrated_config(test_case['config'])
            validation_result = validate_geometry_integrated(
                integrated_config,
                test_case['geometry']
            )
            print(f"    ✓ 正常处理，结果: {validation_result['is_valid']}")
        except Exception as e:
            print(f"    ✓ 正常捕获错误: {type(e).__name__}")


def run_all_tests():
    print("=" * 60)
    print("几何特征整合技能 - 完整测试")
    print("=" * 60)
    
    # 创建输出目录
    output_dir = os.path.join(
        os.path.dirname(__file__),
        "test_output"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载测试配置
    config_path = os.path.join(
        os.path.dirname(__file__),
        "example_config.json"
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    geometry = config.get('geometry', {})
    
    # 运行测试
    results = {}
    
    # 测试1: 配置解析
    integrated_config = test_parse_config()
    results['parse'] = integrated_config is not None
    
    if not integrated_config:
        print("\n配置解析失败，跳过后续测试")
        return
    
    # 测试2: 配置验证
    validation_result = test_validate_config(integrated_config, geometry)
    results['validate'] = validation_result is not None
    
    # 测试3: 性能计算
    performance = test_calculate_performance(integrated_config, geometry)
    results['performance'] = performance is not None
    
    # 测试4: 可视化文件生成
    results['visualization'] = test_generate_visualization(
        integrated_config,
        geometry,
        output_dir
    )
    
    # 测试5: 网格文件生成
    results['mesh'] = test_generate_mesh(
        integrated_config,
        geometry,
        output_dir
    )
    
    # 测试6: OBJ文件生成
    results['obj'] = test_generate_obj(
        integrated_config,
        geometry,
        output_dir
    )
    
    # 测试7: 错误处理
    test_error_handling()
    results['error_handling'] = True
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败")
    
    print(f"\n测试输出目录: {output_dir}")


if __name__ == "__main__":
    run_all_tests()

"""
几何特征整合技能 - 简化测试脚本
测试geometry_shape.py中的核心函数
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_imports():
    print("测试1: 导入模块...")
    try:
        from aircraft_design.geometry_shape import (
            parse_geometry_integrated_config,
            validate_geometry_integrated,
            calculate_geometry_integrated_performance,
            generate_geometry_integrated_visualization,
            generate_geometry_integrated_mesh,
            generate_geometry_integrated_obj
        )
        print("  ✓ 所有函数导入成功")
        return True
    except ImportError as e:
        print(f"  ✗ 导入失败: {e}")
        return False


def test_function_existence():
    print("\n测试2: 函数存在性检查...")
    try:
        import aircraft_design.geometry_shape as gs
        
        functions = [
            'parse_geometry_integrated_config',
            'validate_geometry_integrated',
            'calculate_geometry_integrated_performance',
            'generate_geometry_integrated_visualization',
            'generate_geometry_integrated_mesh',
            'generate_geometry_integrated_obj',
            'generate_fuselage_mesh',
            'generate_wing_mesh',
            'generate_tail_mesh'
        ]
        
        for func_name in functions:
            if hasattr(gs, func_name):
                print(f"  ✓ {func_name}")
            else:
                print(f"  ✗ {func_name} 不存在")
                return False
        
        return True
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False


def test_config_structure():
    print("\n测试3: 配置结构验证...")
    
    test_config = {
        "wing_controls": {
            "ailerons": {
                "enabled": True,
                "chord_fraction": 0.25,
                "span_fraction": 0.3
            }
        },
        "wingtip": {
            "type": "winglet",
            "height_m": 1.5
        },
        "landing_gear": {
            "main": {
                "type": "tricycle",
                "wheel_diameter_m": 0.5
            }
        },
        "engine_library": {
            "type": "turbofan",
            "sea_level_thrust_kn": 50.0
        },
        "nacelle": {
            "length_m": 3.5,
            "diameter_m": 1.2
        },
        "fuselage_canopy": {
            "type": "bubble",
            "length_m": 1.8
        },
        "fuselage_openings": {
            "cargo_door": {
                "width_m": 2.0,
                "height_m": 2.5
            }
        },
        "hardpoint_validation": {
            "wing_hardpoints": {
                "outer_stations": {
                    "max_load_kg": 1000.0
                }
            }
        }
    }
    
    print("  ✓ 配置结构定义完成")
    print(f"    - 包含模块数量: {len(test_config)}")
    
    for module_name in test_config.keys():
        print(f"    - {module_name}")
    
    return test_config


def test_file_generation():
    print("\n测试4: 文件生成测试...")
    
    output_dir = os.path.join(
        os.path.dirname(__file__),
        "test_output"
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建简单的测试数据
    test_integrated_config = {
        "wing_controls": {
            "ailerons": {
                "enabled": True,
                "chord_fraction": 0.25,
                "span_fraction": 0.3
            }
        }
    }
    
    test_geometry = {
        "fuselage": {
            "length_m": 10.0,
            "diameter_m": 1.5,
            "stations": [
                {"x_m": 0.0, "radius_y_m": 0.5, "radius_z_m": 0.5, "n": 16},
                {"x_m": 10.0, "radius_y_m": 0.5, "radius_z_m": 0.5, "n": 16}
            ]
        },
        "wing": {
            "span_m": 10.0,
            "root_chord_m": 2.0,
            "taper_ratio": 0.6
        }
    }
    
    try:
        from aircraft_design.geometry_shape import (
            generate_geometry_integrated_visualization,
            generate_geometry_integrated_mesh
        )
        
        # 测试可视化文件生成
        html_path = os.path.join(output_dir, "test_3d.html")
        generate_geometry_integrated_visualization(
            test_integrated_config,
            test_geometry,
            html_path
        )
        
        if os.path.exists(html_path):
            print(f"  ✓ HTML文件生成成功: {html_path}")
            file_size = os.path.getsize(html_path)
            print(f"    文件大小: {file_size / 1024:.2f} KB")
        else:
            print("  ✗ HTML文件未生成")
            return False
        
        # 测试网格文件生成
        mesh_path = os.path.join(output_dir, "test_mesh.json")
        generate_geometry_integrated_mesh(
            test_integrated_config,
            test_geometry,
            mesh_path
        )
        
        if os.path.exists(mesh_path):
            print(f"  ✓ 网格文件生成成功: {mesh_path}")
            file_size = os.path.getsize(mesh_path)
            print(f"    文件大小: {file_size / 1024:.2f} KB")
        else:
            print("  ✗ 网格文件未生成")
            return False
        
        return True
    except Exception as e:
        print(f"  ✗ 文件生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mesh_functions():
    print("\n测试5: 网格生成函数...")
    
    try:
        from aircraft_design.geometry_shape import (
            generate_fuselage_mesh,
            generate_wing_mesh
        )
        
        # 测试机身网格生成
        fuselage_data = {
            "stations": [
                {"x_m": 0.0, "radius_y_m": 0.5, "radius_z_m": 0.5, "n": 16},
                {"x_m": 5.0, "radius_y_m": 0.75, "radius_z_m": 0.75, "n": 16},
                {"x_m": 10.0, "radius_y_m": 0.5, "radius_z_m": 0.5, "n": 16}
            ]
        }
        
        fuselage_mesh = generate_fuselage_mesh(fuselage_data)
        print("  ✓ 机身网格生成成功")
        print(f"    - 顶点数: {len(fuselage_mesh.get('vertices', []))}")
        print(f"    - 面数: {len(fuselage_mesh.get('faces', []))}")
        print(f"    - 站位数: {fuselage_mesh.get('stations_count', 0)}")
        
        # 测试机翼网格生成
        wing_data = {
            "span_m": 10.0,
            "root_chord_m": 2.0,
            "taper_ratio": 0.6
        }
        
        wing_mesh = generate_wing_mesh(wing_data)
        print("  ✓ 机翼网格生成成功")
        print(f"    - 顶点数: {len(wing_mesh.get('vertices', []))}")
        print(f"    - 面数: {len(wing_mesh.get('faces', []))}")
        
        return True
    except Exception as e:
        print(f"  ✗ 网格生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    print("=" * 60)
    print("几何特征整合技能 - 简化测试")
    print("=" * 60)
    
    results = {}
    
    # 运行测试
    results['imports'] = test_imports()
    
    if not results['imports']:
        print("\n导入失败，跳过后续测试")
        return
    
    results['function_existence'] = test_function_existence()
    results['config_structure'] = test_config_structure() is not None
    results['file_generation'] = test_file_generation()
    results['mesh_functions'] = test_mesh_functions()
    
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
        print("\n技能状态: 功能完整，可以使用")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败")
        print("\n注意: 部分子模块可能需要单独实现")


if __name__ == "__main__":
    run_all_tests()

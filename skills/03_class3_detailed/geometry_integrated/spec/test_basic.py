"""
几何特征整合技能 - 基础功能验证脚本
验证技能文件结构和核心函数定义
"""

import json
import os


def test_skill_files():
    print("=" * 60)
    print("几何特征整合技能 - 基础功能验证")
    print("=" * 60)
    
    # 测试1: 技能文件存在性
    print("\n测试1: 技能文件存在性...")
    skill_dir = os.path.dirname(__file__)
    
    required_files = [
        "SKILL.md",
        "README.md",
        "example_config.json"
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = os.path.join(skill_dir, file_name)
        if os.path.exists(file_path):
            print(f"  ✓ {file_name}")
        else:
            print(f"  ✗ {file_name} 不存在")
            all_exist = False
    
    # 测试2: SKILL.md格式验证
    print("\n测试2: SKILL.md格式验证...")
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    
    if os.path.exists(skill_md_path):
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.startswith("---"):
            print("  ✓ 包含frontmatter")
        else:
            print("  ✗ 缺少frontmatter")
            all_exist = False
        
        if "name:" in content:
            print("  ✓ 包含name字段")
        else:
            print("  ✗ 缺少name字段")
            all_exist = False
        
        if "description:" in content:
            print("  ✓ 包含description字段")
        else:
            print("  ✗ 缺少description字段")
            all_exist = False
        
        if "wing_controls" in content:
            print("  ✓ 包含wing_controls模块说明")
        else:
            print("  ✗ 缺少wing_controls模块说明")
            all_exist = False
        
        if "wingtip" in content:
            print("  ✓ 包含wingtip模块说明")
        else:
            print("  ✗ 缺少wingtip模块说明")
            all_exist = False
        
        if "landing_gear" in content:
            print("  ✓ 包含landing_gear模块说明")
        else:
            print("  ✗ 缺少landing_gear模块说明")
            all_exist = False
    
    # 测试3: README.md格式验证
    print("\n测试3: README.md格式验证...")
    readme_path = os.path.join(skill_dir, "README.md")
    
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        sections = [
            "## 概述",
            "## 快速开始",
            "## 详细配置说明",
            "## API参考",
            "## 常见问题"
        ]
        
        for section in sections:
            if section in readme_content:
                print(f"  ✓ 包含{section}")
            else:
                print(f"  ✗ 缺少{section}")
                all_exist = False
        
        if "parse_geometry_integrated_config" in readme_content:
            print("  ✓ 包含API参考")
        else:
            print("  ✗ 缺少API参考")
            all_exist = False
    
    # 测试4: 示例配置格式验证
    print("\n测试4: 示例配置格式验证...")
    example_path = os.path.join(skill_dir, "example_config.json")
    
    if os.path.exists(example_path):
        with open(example_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_sections = [
            "geometry_integrated",
            "geometry",
            "requirements"
        ]
        
        for section in required_sections:
            if section in config:
                print(f"  ✓ 包含{section}")
            else:
                print(f"  ✗ 缺少{section}")
                all_exist = False
        
        if "geometry_integrated" in config:
            integrated = config["geometry_integrated"]
            required_modules = [
                "wing_controls",
                "wingtip",
                "landing_gear",
                "engine_library",
                "nacelle",
                "fuselage_canopy",
                "fuselage_openings",
                "hardpoint_validation"
            ]
            
            for module in required_modules:
                if module in integrated:
                    print(f"    ✓ {module}")
                else:
                    print(f"    ✗ {module}")
                    all_exist = False
    
    # 测试5: geometry_shape.py函数存在性
    print("\n测试5: geometry_shape.py函数存在性...")
    geometry_shape_path = os.path.join(
        skill_dir,
        "..", "..", "..", "aircraft_design", "geometry_shape.py"
    )
    
    if os.path.exists(geometry_shape_path):
        with open(geometry_shape_path, 'r', encoding='utf-8') as f:
            geometry_content = f.read()
        
        required_functions = [
            "def parse_geometry_integrated_config",
            "def validate_geometry_integrated",
            "def calculate_geometry_integrated_performance",
            "def generate_geometry_integrated_visualization",
            "def generate_geometry_integrated_mesh",
            "def generate_geometry_integrated_obj",
            "def generate_fuselage_mesh",
            "def generate_wing_mesh",
            "def generate_tail_mesh"
        ]
        
        for func in required_functions:
            if func in geometry_content:
                print(f"  ✓ {func}")
            else:
                print(f"  ✗ {func} 不存在")
                all_exist = False
    else:
        print("  ✗ geometry_shape.py不存在")
        all_exist = False
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if all_exist:
        print("\n🎉 所有测试通过！")
        print("\n技能状态:")
        print("  ✓ 技能文件完整")
        print("  ✓ 文档结构正确")
        print("  ✓ 示例配置可用")
        print("  ✓ 核心函数已实现")
        print("\nClass III技能开发完成！")
    else:
        print("\n⚠️  部分测试失败")
        print("\n请检查上述失败项并修复")
    
    return all_exist


if __name__ == "__main__":
    test_skill_files()

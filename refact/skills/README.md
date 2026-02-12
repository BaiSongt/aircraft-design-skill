# 固定翼设计 Skills 总览

本目录包含固定翼飞机设计平台的所有技能（Skills），按照设计阶段和功能模块进行组织。

## 目录结构

```
skills/
├── 00_entry/                    # 主入口
│   ├── overall_sizing_spec/     # 总体设计方案规范
│   ├── overall_sizing_runbook/  # 总体设计执行入口
│   └── advanced_overall_runbook/# 高级总体设计执行入口
│
├── 01_class1_conceptual/        # Class I 概念设计
│   ├── weights/                 # 重量估算
│   │   ├── spec/               # 重量方案规范
│   │   └── runbook/            # 重量闭合执行
│   └── constraints/             # 约束分析
│       ├── spec/               # 约束分析规范
│       └── runbook/            # 约束校核执行
│
├── 02_class2_preliminary/       # Class II 初步设计
│   ├── aero/                    # 气动分析
│   │   ├── spec/               # 气动方案规范
│   │   ├── runbook/            # 气动模型执行
│   │   └── buildup/            # 阻力分解
│   │       ├── spec/           # 阻力分解规范
│   │       └── runbook/        # 阻力分解执行
│   ├── propulsion/              # 推进系统
│   │   ├── spec/               # 推进方案规范
│   │   └── runbook/            # 推进校核执行
│   ├── performance/             # 性能分析
│   │   ├── spec/               # 性能方案规范
│   │   └── runbook/            # 性能校核执行
│   ├── stability_control/       # 稳定与操纵
│   │   ├── spec/               # 稳定操纵规范
│   │   └── runbook/            # 尾翼初算执行
│   ├── structures_loads/        # 结构与载荷
│   │   ├── spec/               # 结构载荷规范
│   │   └── runbook/            # 结构估算执行
│   └── design_loop/             # 设计迭代
│       └── runbook/            # 迭代收敛指导
│
├── 03_class3_detailed/          # Class III 详细设计
│   ├── shape_parametric/        # 外形参数化
│   │   ├── spec/               # 参数化规范
│   │   └── runbook/            # 参数化执行
│   ├── shape_detail/            # 外形详细设计
│   │   ├── spec/               # 详细设计规范
│   │   └── runbook/            # 资产生成执行
│   └── geometry_integrated/     # 几何特征整合
│       └── spec/               # 整合方案规范
│
└── 04_cross_stage/              # 跨阶段工具
    ├── stage2_7_plan/           # 阶段2-7规划
    ├── unified_report/          # 统一报告
    │   └── runbook/            # 报告生成执行
    └── systems/                 # 机载系统
        └── spec/               # 系统配置规范
```

## Skills 分类

### 1. 按类型分类

| 类型 | 说明 | 数量 |
|------|------|------|
| **Spec** | 方案定义：定义输入/输出/约束接口 | 14 |
| **Runbook** | 执行步骤：具体执行与诊断逻辑 | 13 |
| **Plan** | 规划文档：功能分解与验收标准 | 1 |

### 2. 按阶段分类

| 阶段 | 说明 | Skills |
|------|------|--------|
| **Entry** | 主入口 | overall_sizing_spec, overall_sizing_runbook, advanced_overall_runbook |
| **Class I** | 概念设计 | weights_spec/runbook, constraints_spec/runbook |
| **Class II** | 初步设计 | aero_spec/runbook/buildup, propulsion_spec/runbook, performance_spec/runbook, stability_control_spec/runbook, structures_loads_spec/runbook, design_loop_runbook |
| **Class III** | 详细设计 | shape_parametric_spec/runbook, shape_detail_spec/runbook, geometry_integrated_spec |
| **Cross Stage** | 跨阶段工具 | stage2_7_plan, unified_report_runbook, systems_spec |

## 主要入口

### 固定翼总体设计入口

```
fixed_wing_overall_sizing_runbook
```

**执行命令**:
```bash
python -m aircraft_design.run_sizing sizing_input.json --project-name "ProjectName"
```

**功能**:
- 执行 Class I 总体闭环（约束→设计点→重量/性能迭代）
- 收敛后自动进入阶段 2–7 扩展分析
- 生成报告、数据与外形资产

## Skill 元数据规范

每个 SKILL.md 文件包含以下元数据：

```yaml
---
name: "skill_name"              # 技能名称（唯一标识）
description: "技能描述"          # 简短描述
stage: "stage_name"             # 所属阶段
code_module: "module_path"      # 对应代码模块
dependencies:                   # 依赖的其他 skills
  - "dependency_skill_1"
  - "dependency_skill_2"
---
```

### stage 字段取值

- `entry`: 主入口
- `class1_conceptual`: Class I 概念设计
- `class2_preliminary`: Class II 初步设计
- `class3_detailed`: Class III 详细设计
- `cross_stage`: 跨阶段工具

## 依赖关系图

```
fixed_wing_overall_sizing_runbook (主入口)
├── fixed_wing_weights_runbook
│   └── fixed_wing_weights_spec
├── fixed_wing_constraints_runbook
│   └── fixed_wing_constraints_spec
├── fixed_wing_aero_runbook
│   └── fixed_wing_aero_spec
│       └── fixed_wing_aero_buildup_spec
│           └── fixed_wing_aero_buildup_runbook
├── fixed_wing_propulsion_runbook
│   └── fixed_wing_propulsion_spec
├── fixed_wing_performance_runbook
│   └── fixed_wing_performance_spec
├── fixed_wing_stability_control_runbook
│   └── fixed_wing_stability_control_spec
└── fixed_wing_structures_loads_runbook
    └── fixed_wing_structures_loads_spec
```

## 与代码模块的映射

| Skill | 代码模块 |
|-------|---------|
| overall_sizing_runbook | `aircraft_design/run_sizing.py` |
| weights_spec/runbook | `aircraft_design/class1_conceptual/weights_class1.py` |
| constraints_spec/runbook | `aircraft_design/class2_preliminary/constraints.py` |
| aero_spec/runbook | `aircraft_design/class2_preliminary/aero_drag_buildup.py` |
| propulsion_spec/runbook | `aircraft_design/class2_preliminary/propulsion.py` |
| performance_spec/runbook | `aircraft_design/class2_preliminary/performance.py` |
| stability_control_spec/runbook | `aircraft_design/class2_preliminary/stability_control.py` |
| structures_loads_spec/runbook | `aircraft_design/class3_detailed/structures_loads.py` |
| shape_parametric_spec/runbook | `aircraft_design/class3_detailed/geometry_parametric.py` |
| shape_detail_spec/runbook | `aircraft_design/class3_detailed/geometry_detailed.py` |

## 使用指南

### 1. 快速开始

对于新用户，推荐从 `fixed_wing_overall_sizing_runbook` 开始：

1. 准备输入文件 `sizing_input.json`
2. 运行设计闭环
3. 查看输出报告

### 2. 诊断问题

当设计结果不满足要求时：

1. 使用 `fixed_wing_design_loop_runbook` 指导迭代调整
2. 根据具体问题选择对应的 spec/runbook 进行诊断
3. 参考各 skill 中的"诊断路径"章节

### 3. 扩展功能

当需要更高级的分析时：

1. 参考 `fixed_wing_stage2_7_plan` 了解阶段 2-7 的功能
2. 使用 `fixed_wing_advanced_overall_runbook` 进行高级设计
3. 通过 `fixed_wing_geometry_integrated_spec` 配置详细几何特征

## 版本历史

- **v2.0** (2026-02-12): 重构为阶段化目录结构
- **v1.0**: 初始版本，扁平目录结构

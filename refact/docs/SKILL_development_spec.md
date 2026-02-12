# SKILL 开发规范

本文档定义了固定翼设计平台中 SKILL 的开发规范，确保所有 skills 具有一致的结构、命名和元数据。

## 1. 目录结构规范

### 1.1 目录组织

Skills 按照设计阶段组织：

```
skills/
├── 00_entry/                    # 主入口
├── 01_class1_conceptual/        # Class I 概念设计
├── 02_class2_preliminary/       # Class II 初步设计
├── 03_class3_detailed/          # Class III 详细设计
└── 04_cross_stage/              # 跨阶段工具
```

### 1.2 Skill 目录结构

每个 skill 应放在独立的目录中：

```
<功能名>/
├── spec/
│   └── SKILL.md          # 方案定义
└── runbook/
    └── SKILL.md          # 执行步骤
```

对于只有一种类型的 skill：

```
<功能名>/
└── SKILL.md              # 直接放置
```

## 2. 命名规范

### 2.1 Skill 名称

格式：`fixed_wing_<功能>_<类型>`

- **前缀**: `fixed_wing_`（固定翼）
- **功能**: 描述功能的关键词（如 `weights`, `aero`, `constraints`）
- **类型**: `spec` | `runbook` | `plan`

示例：
- `fixed_wing_weights_spec`
- `fixed_wing_weights_runbook`
- `fixed_wing_stage2_7_plan`

### 2.2 目录命名

目录名使用下划线分隔的小写字母：

```
weights/
aero/
shape_parametric/
geometry_integrated/
```

## 3. SKILL.md 文件规范

### 3.1 文件结构

```markdown
---
name: "skill_name"
description: "技能描述"
stage: "stage_name"
code_module: "module_path"
dependencies:
  - "dependency_skill_1"
---

# 标题

## 目标/角色定位

## 输入

## 输出

## 执行步骤/关键规则

## 诊断路径（可选）
```

### 3.2 元数据字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 是 | Skill 唯一标识，与文件名一致 |
| `description` | 是 | 简短描述（不超过 100 字符） |
| `stage` | 是 | 所属阶段 |
| `code_module` | 是 | 对应的代码模块路径 |
| `dependencies` | 否 | 依赖的其他 skills |

### 3.3 stage 字段取值

| 值 | 说明 |
|----|------|
| `entry` | 主入口 |
| `class1_conceptual` | Class I 概念设计 |
| `class2_preliminary` | Class II 初步设计 |
| `class3_detailed` | Class III 详细设计 |
| `cross_stage` | 跨阶段工具 |

## 4. 内容规范

### 4.1 Spec 类型

Spec 定义方案规范，应包含：

1. **目的**: 说明该方案的目标
2. **输入接口**: 定义输入字段
3. **输出接口**: 定义输出字段
4. **关键规则**: 定义约束和验证规则
5. **与统一入口的接口关系**: 说明如何与主入口配合

### 4.2 Runbook 类型

Runbook 定义执行步骤，应包含：

1. **角色定位**: 说明该 skill 在整体流程中的位置
2. **目标**: 说明执行目标
3. **输入要点**: 说明需要的输入
4. **执行步骤**: 具体的执行步骤
5. **输出位置**: 说明输出文件位置
6. **诊断路径**: 说明如何诊断问题

### 4.3 Plan 类型

Plan 定义规划文档，应包含：

1. **目标**: 说明规划目标
2. **功能分解**: 分解为子功能
3. **接口定义**: 定义各子功能的接口
4. **验收标准**: 定义验收标准

## 5. 依赖关系规范

### 5.1 依赖声明

在 `dependencies` 字段中声明依赖：

```yaml
dependencies:
  - "fixed_wing_weights_spec"
  - "fixed_wing_constraints_runbook"
```

### 5.2 依赖规则

1. **Spec 依赖**: Spec 可以依赖其他 Spec
2. **Runbook 依赖**: Runbook 应依赖对应的 Spec
3. **避免循环依赖**: 确保依赖关系是 DAG（有向无环图）

## 6. 与代码模块的映射

### 6.1 映射原则

- 每个 skill 应映射到具体的代码模块
- 一个 skill 可以映射到多个模块
- 多个 skills 可以映射到同一模块

### 6.2 模块路径格式

使用相对于 `aircraft_design/` 的路径：

```yaml
code_module: "aircraft_design/class1_conceptual/weights_class1.py"
```

多个模块用逗号分隔：

```yaml
code_module: "aircraft_design/class2_preliminary/stability_control.py, aircraft_design/class2_preliminary/tail_sizing.py"
```

## 7. 新增 Skill 检查清单

创建新 skill 时，请确认：

- [ ] 目录结构符合规范
- [ ] 命名符合 `fixed_wing_<功能>_<类型>` 格式
- [ ] SKILL.md 包含所有必需的元数据字段
- [ ] stage 字段取值正确
- [ ] code_module 指向正确的代码模块
- [ ] dependencies 声明了所有依赖
- [ ] 内容结构符合类型规范（Spec/Runbook/Plan）
- [ ] 已在 README.md 中更新目录结构

## 8. 示例

### 8.1 Spec 示例

```markdown
---
name: "fixed_wing_weights_spec"
description: "固定翼重量方案（Class I）：空重统计模型 + 航程燃油估算 + MTOW 迭代闭合。"
stage: "class1_conceptual"
code_module: "aircraft_design/class1_conceptual/weights_class1.py"
dependencies:
  - "fixed_wing_overall_sizing_runbook"
---

# 固定翼重量方案（Spec）

## 目标

- 在总体设计早期实现 MTOW（W0）快速闭合
- 输出空重、燃油重量与闭合迭代信息

## 输入

- 航程/任务：`requirements.range_m`
- 推进耗油：`initial_guess.sfc_cruise_1_s`
- 气动极曲线参数：`initial_guess.cd0`、`initial_guess.oswald_e`

## 输出

- `outputs.mtow_kg`
- `outputs.empty_weight_kg`
- `outputs.fuel_weight_kg`

## 关键规则

- 重量、气动、性能必须在同一组几何与工况假设下闭合
```

### 8.2 Runbook 示例

```markdown
---
name: "fixed_wing_weights_runbook"
description: "执行固定翼 Class I 重量闭合（W0/We/Wf）并输出收敛信息。"
stage: "class1_conceptual"
code_module: "aircraft_design/class1_conceptual/weights_class1.py"
dependencies:
  - "fixed_wing_weights_spec"
---

# 固定翼重量闭合执行（Runbook）

## 角色定位

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 闭环驱动

## 步骤

1. 运行总体入口，获取 `output/<project>_*/design_data.json`
2. 读取 `outputs.mtow_kg / empty_weight_kg / fuel_weight_kg`
3. 如果燃油/空重异常，按优先级排查

## 诊断路径

- 推进耗油单位 → `L/D`（`cd0/e/AR`）→ 任务指标是否过激
```

## 9. 版本历史

- **v2.0** (2026-02-12): 重构为阶段化目录结构，新增元数据规范
- **v1.0**: 初始版本

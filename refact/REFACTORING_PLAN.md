# 飞机设计平台代码重构计划 (Aircraft Design Platform Refactoring Plan)

## 1. 目标与动机 (Objective & Motivation)

当前的代码库是一个功能强大、模块丰富的飞机设计平台。为了提升其架构的清晰度、可维护性和未来可扩展性，我们启动本次重构。

核心目标是：
1.  **流程阶段化**: 将单一的设计流程分解为串行的、不同保真度的阶段 (Class I, II, III...)。
2.  **代码结构化**: 将 `aircraft_design` 目录下的扁平文件结构，按照功能和设计阶段进行分组，整理到子目录中。
3.  **输出规范化**: 实现统一的、带时间戳的结构化输出，方便结果追溯和对比。
4.  **架构可扩展**: 确保新架构可以轻松地在未来加入更高保真度的设计阶段（如 Class IV MDO）。

---

## 2. 重构执行方案 (Execution Plan)

我们将重构分为四个明确的阶段执行。

### 第一阶段：分析与规划 (Phase 1: Analysis & Planning)

**目标**: 在不修改任何代码的情况下，完成现状分析并制定出具体、可行的重构蓝图。

1.  **关键代码分析**: 深入理解现有核心逻辑、执行入口和测试方法。
    *   主入口: `run_sizing.py`
    *   核心算法: `aircraft_design/design_loop_orchestrator.py`, `aircraft_design/sizing.py`
    *   关键模块: `aircraft_design/weights_class1.py`, `aircraft_design/openvsp_bridge.py`
    *   测试用例: `tests/test_systems_e2e.py`

2.  **设计新目录结构**: 规划 `aircraft_design` 内部的新结构，对现有py文件进行分类。
    ```
    aircraft_design/
    ├── __init__.py
    ├── common/          # 通用工具 (units, atmosphere, formulas)
    ├── config/          # 配置与库 (engine_library, airfoil_library)
    ├── class1_conceptual/ # Class I: 概念设计 (weights_class1)
    ├── class2_preliminary/ # Class II: 初步设计 (sizing, performance, aero_drag, etc.)
    ├── class3_detailed/   # Class III: 详细分析 (openvsp_bridge, vspaero_interface)
    └── utils/           # 辅助工具 (report_generator, visualization)
    ```

3.  **获取批准**: 将详细的目录和文件映射方案提交确认，通过后方可进入下一阶段。

### 第二阶段：代码与目录重构 (Phase 2: Code & Directory Restructuring)

**目标**: 物理上重新组织代码库，并修复所有因此产生的引用问题。

1.  **创建目录**: 使用 `mkdir` 命令创建在第一阶段规划的所有新子目录。
2.  **移动文件**: 推荐使用 `git mv` 命令移动文件，以保留git历史记录。
3.  **修复 `import` 语句**: 系统性地修正所有因文件移动而失效的 `import` 语句。这是本阶段最核心的工作。重点关注 `aircraft_design` 和 `tests` 目录下的所有文件。

### 第三阶段：实施新工作流编排器 (Phase 3: Workflow Orchestrator Implementation)

**目标**: 创建新的主控脚本，将重构后的模块化代码串联成新的、可扩展的工作流。

1.  **创建主控脚本**: 在项目根目录创建 `run_multiclass_design.py`。
2.  **实现主控逻辑**: 脚本将负责：
    *   创建带时间戳的输出总目录 (`output/aircraft_sizing_YYYYMMDD_HHMMSS/`)。
    *   为每个Class创建子目录 (`class1/`, `class2/`, ...)。
    *   按顺序调用每个Class阶段的入口函数。
    *   通过标准化的JSON文件在阶段间传递数据。
3.  **封装阶段入口**: 确保每个Class模块都提供一个统一的入口函数，遵循标准接口：
    ```python
    def execute_stage(input_data_path: str, output_directory: str) -> str:
        """
        执行一个设计阶段。
        
        Args:
            input_data_path (str): 上一阶段输出的JSON文件路径。
            output_directory (str): 当前阶段用于存放所有输出的目录。

        Returns:
            str: 当前阶段生成的核心输出JSON文件路径。
        """
        # ... 实现该阶段的逻辑 ...
        pass
    ```

### 第四阶段：集成测试与验证 (Phase 4: Integration Testing & Verification)

**目标**: 确保整个重构后的系统作为一个整体，能够正确、稳定地运行。

1.  **改造测试用例**: 修改现有的端到端测试用例 (`test_systems_e2e.py`)：
    *   更新 `import` 语句以匹配新的文件结构。
    *   将测试目标从调用旧脚本改为调用新的 `run_multiclass_design.py`。
    *   修改测试断言，以验证新的结构化输出目录和文件内容。
2.  **执行集成测试**: 使用 `pytest` 运行改造后的测试。
    ```bash
    pytest tests/test_systems_e2e.py
    ```
3.  **调试与修复**: 循环执行“测试-分析失败-修复代码”的流程，直到所有集成测试用例通过。

---
通过遵循此计划，我们将把项目重构为一个更健壮、更清晰、更易于扩展的飞机设计平台。

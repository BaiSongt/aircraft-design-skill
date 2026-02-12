---
name: "fixed_wing_constraints_runbook"
description: "执行固定翼约束校核并给出设计点调整建议。当用户关心起降/失速/巡航/爬升约束是否满足或要定位卡点时调用。"
stage: "class1_conceptual"
code_module: "aircraft_design/class2_preliminary/constraints.py"
dependencies:
  - "fixed_wing_constraints_spec"
---

# 固定翼约束分析执行（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 驱动：约束用于修正/验证设计点（W/S、T/W）。
- 单独调用用于解释“哪个约束在驱动设计点”，以及“该改哪个输入字段”。

## 输出位置（以统一入口输出为准）

- `output/<project>_*/design_report_v2.md`：可读的约束/设计点总结（若对应章节已输出）
- `output/<project>_*/design_data.json`：设计点与迭代信息（`inputs.initial_guess`、`outputs`）

## 迭代建议

- `stall_ws` 裕度不足：降低 `wing_loading_pa` 或提高 `cl_max`
- `cruise` 余度不足：降低 `cd0`、提高 `e/AR` 或提高推重比
- `climb_gradient` 余度不足：提高推重比或降低重量/阻力
- `takeoff_distance` 裕度不足：提高推重比或提高起飞构型 `CLmax`
- `landing_distance` 裕度不足：提高着陆构型 `CLmax` 或放宽着陆距离
## 几何约束校核

除了性能约束外，还应校核几何约束。调用 `aircraft_design/geometry_constraints.py` 进行检查：

1.  **燃油容积**：机翼内部可用体积 >= 任务所需燃油体积。
2.  **展弦比**：AR <= 结构或停机位限制。

```python
from aircraft_design.geometry_constraints import GeometryConstraintChecker
# ... 实例化 checker ...
results = checker.check_all()
```

---
name: "fixed_wing_constraints_runbook"
description: "执行固定翼约束校核并输出设计点余度。当需要快速判断给定 W/S、T/W 是否满足巡航/爬升/失速/起降距离约束时调用。"
---

# 固定翼约束分析执行（Runbook）

## 推荐入口

- 一键总体脚本：`aircraft_design/run_sizing.py`

## 输出位置

- `out/results.json` 的 `constraints` 字段
- `out/report.md` 的“约束校核”章节

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

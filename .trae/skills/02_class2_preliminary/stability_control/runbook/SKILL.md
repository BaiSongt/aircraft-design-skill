---
name: "fixed_wing_stability_control_runbook"
description: "执行尾翼初算（尾容积系数法）并输出 Sh/Sv。当总体设计需要尾翼面积初值或静稳定裕度不足需调整尾容积时调用。"
stage: "class2_preliminary"
code_module: "aircraft_design/class2_preliminary/stability_control.py, aircraft_design/class2_preliminary/tail_sizing.py"
dependencies:
  - "fixed_wing_stability_control_spec"
---

# 固定翼稳定与操纵初算执行（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 在扩展阶段驱动。
- 单独调用用于快速估算“尾翼面积需要多大”，以及为后续静稳定/配平/阻力增量留接口。

## 输入

- `tail.vh`, `tail.vv`
- `tail.lh_m`, `tail.lv_m`
- 机翼几何：来自总体计算的 `s_m2`, `b_m`, `cbar_m`

## 输出

- `tail.sh_m2`, `tail.sv_m2`

## 动态稳定性分析 (New)

在获得尾翼尺寸后，调用 `aircraft_design/stability_dynamic.py` 进行模态分析：

1.  计算纵向模态（短周期、长周期）。
2.  计算横航向模态（荷兰滚、滚转、螺旋）。
3.  评定飞行品质等级（Level 1/2/3）。

```python
from aircraft_design.stability_dynamic import DynamicStabilityAnalyzer
# ... 实例化 analyzer ...
results = analyzer.analyze(...)
```

## 推荐入口

- 统一入口：`fixed_wing_overall_sizing_runbook`

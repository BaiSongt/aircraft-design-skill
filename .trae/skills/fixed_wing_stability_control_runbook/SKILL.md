---
name: "fixed_wing_stability_control_runbook"
description: "执行固定翼尾翼初算（尾容积系数法）并输出 Sh/Sv。当需要快速得到尾翼面积初值用于总体迭代时调用。"
---

# 固定翼稳定与操纵初算执行（Runbook）

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

- 一键总体脚本：`scripts/run_fixed_wing_design.py`


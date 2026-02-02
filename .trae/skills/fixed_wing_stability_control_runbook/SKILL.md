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

## 推荐入口

- 一键总体脚本：`scripts/run_fixed_wing_design.py`


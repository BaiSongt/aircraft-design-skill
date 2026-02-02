---
name: "fixed_wing_constraints_runbook"
description: "执行固定翼约束校核并输出设计点余度。当需要快速判断给定 W/S、T/W 是否满足巡航/爬升/失速/起降距离约束时调用。"
---

# 固定翼约束分析执行（Runbook）

## 推荐入口

- 一键总体脚本：`scripts/run_fixed_wing_design.py`

## 输出位置

- `out/results.json` 的 `constraints` 字段
- `out/report.md` 的“约束校核”章节

## 迭代建议

- `stall_ws` 裕度不足：降低 `wing_loading_pa` 或提高 `cl_max`
- `cruise` 余度不足：降低 `cd0`、提高 `e/AR` 或提高推重比
- `climb_gradient` 余度不足：提高推重比或降低重量/阻力
- `takeoff_distance` 裕度不足：提高推重比或提高起飞构型 `CLmax`
- `landing_distance` 裕度不足：提高着陆构型 `CLmax` 或放宽着陆距离
- `takeoff_climb_gradient` 裕度不足：提高推重比或降低起飞构型阻力增量

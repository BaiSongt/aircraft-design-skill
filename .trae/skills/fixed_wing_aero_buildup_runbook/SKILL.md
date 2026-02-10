---
name: "fixed_wing_aero_buildup_runbook"
description: "执行固定翼气动阻力分解计算。当需要从几何参数计算详细阻力清单时调用。"
---

# 固定翼气动阻力分解执行步骤（Runbook）

## 角色定位（统一入口）

- 本技能默认由 `fixed_wing_overall_sizing_runbook` 在“收敛后的阶段 2–7 扩展分析”中自动执行（Stage2 Aero）。
- 单独调用用于回答两类问题：
  - “我填的 `initial_guess.cd0` 是否合理？如果不合理，哪一部分在贡献阻力？”
  - “能否用几何可追溯的 CD0 替代拍脑袋的 CD0？”

## 计算模型（以代码为准）

- 部件级 buildup：`aircraft_design/aero_drag_buildup.py`
  - 输出 `cd0` 及 `Fuselage/Wing/Horizontal Tail/Vertical Tail/Misc/Wave Drag` 分解

## 输入要点（来自统一输入 JSON）

- `requirements.cruise_altitude_m`、`requirements.cruise_mach`：巡航工况
- `initial_guess.thickness_ratio`、`initial_guess.sweep_deg`、`initial_guess.aspect_ratio`、`initial_guess.taper_ratio`
- 几何（优先级从高到低）：
  - `geometry_shape` / `geometry_detailed`（最可追溯）
  - 若未提供，则由总体闭环的几何派生模块给出默认量级

## 执行方式

- 统一入口运行：`fixed_wing_overall_sizing_runbook`
- 重点关注收敛后是否进入扩展阶段（未收敛则不会生成阻力分解结果）

## 输出位置与读取

- `output/<project>_*/advanced_design_results_*.json`：
  - `stage2_aero.cd0`、`stage2_aero.cd0_breakdown`、`stage2_aero.wave_drag`
- `output/<project>_*/advanced_design_report.md`：可读的阻力分解表

## 常见诊断

- `cd0` 明显过大：优先检查机身尺度（长度/直径）与 `thickness_ratio`
- 波阻占比异常：检查巡航 Mach 与后掠/厚度比是否匹配
- 机翼/尾翼占比异常：检查面积比（尾翼相对翼面积）与外形细化输入是否缺失

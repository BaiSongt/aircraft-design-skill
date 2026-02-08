---
name: "fixed_wing_aero_buildup_spec"
description: "固定翼气动阻力分解方案：基于几何外形的部件级阻力叠加（CD0 Buildup）。当需要用物理模型替代用户猜测的 CD0 时调用。"
---

# 固定翼气动阻力分解方案（Spec）

## 目标

- 替代用户猜测的 `cd0`，实现基于几何参数的物理估算。
- 提供详细的阻力分解表（摩擦、压差、干扰、波阻）。
- 支持从 Class I (Sizing) 到 Class II (Detailed) 的平滑过渡。

## 输入 (Input)

- `geometry_shape` (来自 `fixed_wing_shape_parametric` 或 `detailed`)
  - 机身: `length_m`, `diameter_m`, `wetted_area_m2` (若无则估算)
  - 机翼: `s_ref_m2`, `s_exposed_m2`, `span_m`, `root_chord_m`, `tip_chord_m`, `sweep_deg`, `t_c`
  - 尾翼: 同机翼
- `flight_conditions`
  - `altitude_m`: 飞行高度
  - `mach`: 马赫数
  - `velocity_m_s`: 速度 (可选，与 mach 二选一)

## 输出 (Output)

- `aero.cd0`: 总零升阻力系数
- `aero.drag_breakdown`:
  - `parasite_drag`: { `fuselage`, `wing`, `htail`, `vtail`, `nacelle` }
  - `wave_drag`: (若 M > M_crit)
  - `misc_drag`: (起落架、冷却阻力等，可选)
- `aero.l_d_cruise`: 基于新 CD0 的升阻比估算

## 算法逻辑 (Methodology)

1. **几何预处理**: 计算部件的雷诺数特征长度、浸湿面积、形状因子参数。
2. **摩擦阻力 (Friction)**: 平板湍流/层流公式 (e.g., Prandtl-Schlichting)。
3. **形状阻力 (Form)**: 应用形状因子 (Form Factors, e.g., Raymer Eq 12.30-12.32)。
4. **干扰阻力 (Interference)**: 应用干扰因子 (Q Factors)。
5. **波阻 (Wave)**: 跨音速/超音速时的简单的 Korn equation 或 Sears-Haack 近似（Phase 1 可选）。
6. **汇总**: $C_{D0} = \frac{1}{S_{ref}} \sum (C_{f,i} \cdot FF_i \cdot Q_i \cdot S_{wet,i}) + C_{D,wave} + C_{D,misc}$

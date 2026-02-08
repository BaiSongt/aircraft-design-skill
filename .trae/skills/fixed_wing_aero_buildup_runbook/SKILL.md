---
name: "fixed_wing_aero_buildup_runbook"
description: "执行固定翼气动阻力分解计算。当需要从几何参数计算详细阻力清单时调用。"
---

# 固定翼气动阻力分解执行步骤（Runbook）

## 1. 准备几何数据
- 检查 `geometry_shape` 是否存在。若仅有 `sizing` 输入，需调用 `fixed_wing_shape_parametric` 生成默认几何。
- 关键参数检查：`wetted_area` 是否已计算？若为 `null`，需使用简易公式估算（如 Raymer wetted area correlations）。

## 2. 确定大气环境
- 根据 `altitude_m` 计算 `density`, `viscosity`, `speed_of_sound`。
- 计算 `Re` (Reynolds Number) per unit length。

## 3. 部件循环计算
对每个部件 (Fuselage, Wing, HTail, VTail):
1. **特征长度 ($L$)**: 机身为长度，翼面为 MAC。
2. **雷诺数 ($Re_L$)**: $Re_L = \frac{\rho V L}{\mu}$。
3. **摩擦系数 ($C_f$)**:
   - 湍流: $C_f = \frac{0.455}{(\log_{10} Re_L)^{2.58} (1 + 0.144 M^2)^{0.65}}$
4. **形状因子 ($FF$)**:
   - 机身: $FF = 1 + \frac{60}{(L/d)^3} + 0.0025 (L/d)$
   - 翼面: $FF = 1 + L(t/c) + 100(t/c)^4$ (含后掠修正)
5. **干扰因子 ($Q$)**:
   - 机身: 1.0
   - 机翼: 1.0 (高单翼/低单翼不同)
   - 尾翼: 1.03-1.05
6. **部件阻力面积 ($f$)**: $f = C_f \cdot FF \cdot Q \cdot S_{wet}$

## 4. 杂项阻力叠加
- 泄漏与凸起 (Leaks & Protuberances): 增加 5-10% 的总 $f$。

## 5. 计算 $C_{D0}$
- $C_{D0} = \frac{\sum f}{S_{ref}}$

## 6. 输出与验证
- 检查 $C_{D0}$ 是否在合理范围 (0.015 - 0.040 for typical jets)。
- 若异常，检查 $S_{wet}$ 是否过大或 $S_{ref}$ 定义错误。

# 固定翼气动外形深度细化计划 (Advanced Aerodynamic Shape Design)

**版本**: 1.1 (Implemented)
**日期**: 2026-02-01
**参考资料**:
- Raymer, D. P. *Aircraft Design: A Conceptual Approach* (Chapter 6: Geometry Sizing, Chapter 7: Lofting)
- Roskam, J. *Airplane Design* (Part II: Preliminary Configuration Design)
- Gudmundsson, S. *General Aviation Aircraft Design*

---

## 1. 现状分析 (Current State Analysis)

系统已升级至“准工程级气动外形”能力，支持 Class II 阶段的详细几何定义与分析。

| 组件 | 当前功能 | 升级后能力 |
| :--- | :--- | :--- |
| **机身 (Fuselage)** | 参数化截面与线型 | 支持超椭圆截面 ($n$参数)；支持长细比驱动的机头/机尾生成；支持座舱盖（Canopy）隆起。 |
| **机翼 (Wing)** | 梯形/多段 | 支持翼身融合整流（Fairing/Fillet）模拟。 |
| **分析 (Analysis)** | 基础几何参数 | 支持面积律（Area Rule）截面积分布计算；支持几何硬点约束检查。 |

---

## 2. 细化目标与路线图 (Roadmap Status)

### 阶段 8：机身截面与线型进化 (Fuselage Advanced Shaping)
- [x] **8.1 超椭圆截面 (Super-Ellipse/Fuselage Sections)**
  - 支持 $n$ 参数控制截面形状。
- [x] **8.2 纵向线型控制 (Longitudinal Shaping)**
  - 实现 `parametric` 模式，支持 Nose/Tail Fineness Ratio。
  - 支持 `canopy` 修正器，生成驾驶舱隆起。
- [x] **8.3 面积律分析 (Area Rule)**
  - 实现 `calculate_cross_sectional_area_distribution` 函数，计算机身+机翼+尾翼的总截面积分布。

### 阶段 9：部件融合与整流 (Integration & Fairing)
- [x] **9.1 翼身融合 (Wing-Body Fairing/Fillet)**
  - 实现 `wing_fairing` 修正器，在翼根处增加机身宽度以模拟整流。
- [x] **9.2 尾椎与过渡 (Tail Cone)**
  - 通过 Phase 8.2 的尾部线型控制实现。

### 阶段 10：内部约束驱动 (Constraint-Driven Geometry)
- [x] **10.1 关键硬点 (Hardpoints)**
  - 实现 `verify_geometric_constraints` 函数，检查关键点（飞行员、发动机等）是否位于机身包络内。

---

## 3. 接口说明 (API Reference)

### 几何输入扩展 (Input Schema)

```json
"fuselage": {
    "profile": {
        "mode": "parametric",
        "nose_fineness_ratio": 1.5,
        "tail_fineness_ratio": 2.5,
        "nose_shape": "ellipsoid",
        "tail_shape": "conical"
    },
    "modifiers": {
        "canopy": {
            "x_rel": 0.2,
            "length_rel": 0.15,
            "height_m": 0.3
        },
        "wing_fairing": {
            "radius_m": 0.15
        }
    }
}
```

### 约束检查 (Constraints)

```python
violations = verify_geometric_constraints(geometry, {
    "hardpoints": {
        "pilot_eye": {"x": 2.5, "y": 0.0, "z": 0.8}
    }
})
```

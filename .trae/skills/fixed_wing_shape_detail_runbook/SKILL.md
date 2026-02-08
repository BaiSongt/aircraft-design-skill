---
name: "fixed_wing_shape_detail_runbook"
description: "执行固定翼外形详细设计的产物生成（翼型/机身剖面/三视图HTML/创成式搜索/OpenVSP脚本）。用户要一键产出外形资产并验证时调用。"
---

# 固定翼外形详细设计（Runbook）

## 目标

- 从单一输入 JSON 出发，生成可复用外形资产与可视化
- 支持创成式外形搜索（候选集 + 每个候选的三视图预览）
- 支持 OpenVSP 脚本导出（可选在 OpenVSP Python 环境执行）

## 一键运行

### 1) 生成外形资产 + 三视图预览

```bash
python ./scripts/run_fixed_wing_design.py ./examples/fixed_wing_ga_single.json
```

产物（`out/`）：

- `geometry_3d.html`：三视图预览
- `geometry.obj`：OBJ 资产
- `geometry_mesh.json`：网格 JSON

### 2) 生成 OpenVSP 脚本

```bash
python ./scripts/generate_openvsp_script.py ./examples/fixed_wing_ga_single.json --out ./out/openvsp_generate.py
```

如在 OpenVSP 的 Python 环境中，可加 `--run` 直接生成 `generated.vsp3`。

### 3) 创成式外形搜索（候选集）

```bash
python ./scripts/shape_search.py ./examples/fixed_wing_ga_single.json --n 32 --seed 1
```

产物（`out/`）：

- `shape_search_report.md`：Top 候选表格（含 3D 链接）
- `shape_search_results.json`：全部候选与可行集
- `shapes/shape_*.html`：每个候选的三视图预览

## GUI 关系说明

- 本 Runbook 生成的是离线外形资产与 HTML 预览，不会自动推送到 GUI
- 若需要 GUI 实时显示，请使用总体设计 Runbook 的 GUI 流程并确保输入含 `geometry_shape` 或 mesh

## 输入片段示例（用于 GUI 兼容）

```json
{
  "geometry_shape": {
    "fuselage": {
      "axis": {"length_m": 10.0},
      "profile": {"mode": "parametric", "max_radius_m": 1.2}
    },
    "wing": {
      "planform": {
        "s_ref_m2": 24.0,
        "aspect_ratio": 6.0,
        "taper_ratio": 0.5,
        "sweep_quarter_chord_deg": 15.0
      }
    }
  }
}
```

## 验证

```bash
python -m unittest discover -s tests
```

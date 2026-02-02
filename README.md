# aircraft-design-skill

该仓库提供一个用于飞机总体设计的 SKILL + Python 计算内核组合，优先覆盖固定翼总体设计的快速方案生成与可执行计算流程。

## 能力概览

- 固定翼总体设计闭环：约束 → 设计点 → 初步尺寸 → 气动 → 重量 → 性能 → 稳定 → 结构 → 优化
- 统一输入/输出：JSON 输入，输出 results.json + report.md + 几何可视化
- 可视化与几何：三视图/轴测 HTML、网格、OBJ 与 OpenVSP 脚本

## 运行环境

- Python 3.12

## 快速开始

1. 准备输入（示例见 examples/fixed_wing_ga_single.json）
2. 运行：

```powershell
python .\scripts\run_fixed_wing_design.py .\examples\fixed_wing_ga_single.json
```

3. 结果输出到 out/：

- out/results/results.json
- out/report/report.md
- out/report/constraints_ws_tw.svg
- out/geometry/geometry_3d.html
- out/geometry/geometry.obj
- out/mesh/geometry_mesh.json
- out/openvsp/openvsp_advanced.py
- out/report/area_rule_report.md

## 输入说明（要点）

示例输入见 examples/fixed_wing_ga_single.json，常用字段如下：

- mission：航程/高度/速度/起降/储备油等任务参数
- payload/crew：载荷与机组重量
- aero：cd0、e、cl_max 等气动假设
- sizing：wing_loading_pa、aspect_ratio、thrust_to_weight
- weights：空重统计模型参数与初始重量
- propulsion：推进类型与耗油/效率
- geometry/geometry_detailed/geometry_shape：几何输入与细化外形
- tail/stability/structures：稳定、结构与载荷参数
- design_loop：网格搜索设置
- openvsp：OpenVSP 脚本输出与可选执行

## 设计点网格搜索

```powershell
python .\scripts\run_fixed_wing_design.py .\examples\fixed_wing_ga_single.json --grid-search
```

网格搜索读取 design_loop.wing_loading_pa_grid、design_loop.aspect_ratio_grid、design_loop.thrust_to_weight_grid，并在输出中追加 design_loop.best_sizing、candidates、top_candidates、sensitivity。

## 输出结构

out/ 目录下分为以下子目录：

- results/：results.json（总体计算结果与中间字段）
- report/：report.md、constraints_ws_tw.svg、area_rule_report.md
- geometry/：geometry_3d.html、geometry.obj、advanced_shape_results.json
- mesh/：geometry_mesh.json
- openvsp/：openvsp_advanced.py 与 openvsp_generate.py

## 几何与可视化

- geometry_3d.html 为独立 HTML，可直接打开查看三视图与轴测。
- 当 geometry_shape/geometry_detailed 信息完整时，会生成更细的网格与控制面预览。
- 如需离线加载 Three.js，可在调用 generate_three_view_html 时传入 resource_config（prefer_local、local_base_url），或在生成 HTML 前替换资源路径。

## OpenVSP

生成 OpenVSP 脚本：

```powershell
python .\scripts\generate_openvsp_script.py .\examples\fixed_wing_ga_single.json --out .\out\openvsp_generate.py
```

可追加 --run 在已安装 OpenVSP 的环境中直接执行脚本。

## 其他脚本

- 随机外形搜索：scripts/shape_search.py <input.json> [--n N] [--seed S]
- 高级外形示例：scripts/run_advanced_shape_demo.py

## 测试与质量

```powershell
python -m unittest discover -s tests
```

```powershell
ruff check .
ruff format --check .
mypy aircraft_design/
```

## 目录结构

- .trae/skills/：总体设计各板块的方案与执行 SKILL
- aircraft_design/：Python 计算模块
- examples/：示例输入
- scripts/：运行脚本与工具
- tests/：单元测试


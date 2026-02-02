## Step 2：气动外形设计（创成式，OpenVSP 参考）规划

### 目标

- 在总体设计基础上，引入“参数化几何→外形生成→气动/阻力→反馈”的闭环
- 保持 OpenVSP 为可选集成：可生成 OpenVSP 脚本/模型文件，不强依赖本机安装
- 输出字段可追溯，能够驱动阻力分解、构型增量与后续更高保真分析（VSPAero/CFD）

### 模块边界

- `aircraft_design.geometry_parametric`
  - 参数化几何数据模型（翼/机身/尾翼）
  - 派生几何量（Sref、b、cbar、湿面积、尾翼面积比例等）
  - 输出到 OpenVSP Python 脚本（生成 .vsp3）
- `aircraft_design.openvsp_bridge`
  - OpenVSP 可选桥接：检测/写脚本/（可选）在 OpenVSP Python 环境运行
- `aircraft_design.aero_drag_buildup`
  - 使用几何假设生成可追溯的 `cd0` 分解

### 输入接口（建议）

- 顶层新增 `geometry_parametric`
  - `wing.aspect_ratio`
  - `wing.taper_ratio`
  - `wing.sweep_quarter_chord_deg`
  - `wing.t_c`
  - `fuselage.length_m`
  - `fuselage.diameter_m`
  - `tail.area_ratio_to_wing`
- 可选 `openvsp`
  - `enabled`
  - `script_out_path`
  - `run`（是否尝试执行脚本，默认 false）

### 输出接口（建议）

- `geometry_parametric`（输入快照）
- `geometry_derived`
  - `s_ref_m2` `b_m` `cbar_m`
  - `s_wet_*` 湿面积
  - `wetted_area_factor`
- `openvsp`
  - `script_path`
  - `ran` / `error`

### 验收标准

- 不安装 OpenVSP 时：能生成脚本并完成总体设计闭环，报告包含几何与阈值信息
- 安装 OpenVSP 时：可一键跑脚本生成 `generated.vsp3`，且生成模型可打开
- `cd0_buildup` 随外形尺寸/厚度/尾翼比例变化趋势合理


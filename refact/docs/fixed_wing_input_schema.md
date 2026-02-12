# 固定翼输入字段（JSON）

## 顶层

- `aircraft_role`：字符串，可选
- `mission`：任务与关键约束（必需）
- `payload`：载荷（必需）
- `crew`：机组（必需）
- `aero`：一级气动模型参数（必需）
- `sizing`：设计点与初步几何相关参数（必需）
- `weights`：重量模型参数（必需）
- `propulsion`：推进类型与耗油/效率（必需）
- `geometry`：几何与阻力分解假设（可选）
- `tail`：尾翼初算输入（可选）
- `stability`：稳定与操纵输入（可选）
- `structures`：结构与载荷输入（可选）
- `design_loop`：设计迭代输入（可选）

## mission

- `range_m`
- `cruise_altitude_m`
- `cruise_speed_m_s`
- `v_stall_m_s`
- `v_climb_m_s`（可选，默认 `1.3 * v_stall_m_s`）
- `climb_gradient`（可选，默认 `0.024`）
- `takeoff_distance_m`（可选）
- `landing_distance_m`（可选）
- `mu_takeoff`（可选，默认 `0.04`）
- `landing_decel_g`（可选，默认 `0.4`）
- `takeoff_climb_gradient`（可选，默认等于 `climb_gradient`）
- `obstacle_height_m`（可选，默认 `15.24`）
- `landing_approach_angle_deg`（可选，默认 `3.0`）
- `runway_slope`（可选，默认 `0.0`；上坡为正，量纲为坡度）
- `headwind_m_s`（可选，默认 `0.0`；顶风为正）
- `high_lift_takeoff`（可选；字符串，优先指定起飞构型）
- `high_lift_landing`（可选；字符串，优先指定着陆构型）
- `loiter_time_s`（可选，默认 `0.0`）
- `loiter_speed_m_s`（可选，默认等于 `cruise_speed_m_s`）
- `alternate_range_m`（可选，默认 `0.0`）

## aero

- `cd0`
- `e`
- `cl_max`

## sizing

- `wing_loading_pa`
- `aspect_ratio`
- `thrust_to_weight`

## weights

- `empty_a`
- `empty_b`
- `reserve_fraction`（可选）
- `w0_guess_kg`（可选）

## propulsion

- `type`：`prop` 或 `jet`
- 若 `prop`：
  - `sfc_1_s`
  - `prop_efficiency`
- 若 `jet`：
  - `tsfc_1_s`
  - `thrust_sl_n`（可选；若缺省可由 `thrust_to_weight` 与 MTOW 推得）

## geometry（可选）

- `fuselage_length_m`
- `fuselage_diameter_m`
- `wetted_area_factor`
- `wing_t_c`
- `tail_area_ratio`

## tail（可选）

- `vh`
- `vv`
- `lh_m`
- `lv_m`

## stability（可选）

- `x_ac_w_cbar`（可选，默认 0.25）
- `x_cg_cbar`（可选，默认 0.30）
- `x_cg_fwd_cbar`（可选；若提供则输出 CG 包线静稳定范围）
- `x_cg_aft_cbar`（可选）
- `cm0_w`（可选）
- `tail_efficiency`（可选）
- `downwash_deda`（可选）
- `a_ratio`（可选）

## structures（可选）

- `n_limit`（可选，默认 3.8）
- `wing_t_c`（可选，默认 0.12）
- `enable_weight_feedback`（可选，默认 false）
- `baseline_struct_frac`（可选，默认 0.30）
- `feedback_gain`（可选，默认 1.0）

## design_loop（可选）

- `wing_loading_pa_grid`（可选）
- `aspect_ratio_grid`（可选）
- `thrust_to_weight_grid`（可选）
- `objective`（可选；`min_w0_kg|min_wf_kg|max_ld|max_min_margin`）
- `top_n`（可选）
- `sensitivity_steps`（可选；字典）

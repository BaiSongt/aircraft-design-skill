import json
from datetime import datetime


def generate_advanced_design_report(result_file: str, output_file: str):
    with open(result_file, "r") as f:
        data = json.load(f)

    report = []

    report.append("# 超音速飞机二阶段高级设计报告")
    report.append("")
    report.append("**项目名称**: Supersonic4Mach")
    report.append(f"**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("**版本**: V3.1 (Advanced Design - Stage 2-7 - Dynamic)")
    report.append("")
    report.append("---")
    report.append("")

    report.append("## 执行摘要")
    report.append("")
    report.append("本报告基于一阶段总体设计结果，执行了二阶段高级设计分析，包括以下七个阶段：")
    report.append("")
    report.append("1. **阶段2**: 气动阻力分解与构型增量")
    report.append("2. **阶段3**: 推进随工况变化模型")
    report.append("3. **阶段4**: 任务剖面耗油分解")
    report.append("4. **阶段5**: 稳定与配平分析")
    report.append("5. **阶段6**: 结构与载荷分析")
    report.append("6. **阶段7**: 迭代与敏感性/优化")
    report.append("")
    report.append("---")
    report.append("")

    # --- Stage 2 ---
    report.append("## 阶段2: 气动阻力分解与构型增量")
    report.append("")
    report.append("### 2.1 阻力分解")
    report.append("")
    stage2 = data["stage2_aero"]
    report.append("| 阻力分量 | 数值 | 占比 |")
    report.append("|:---|:---:|:---:|")
    bd = stage2["cd0_breakdown"]
    cd0_fuse = bd.get("Fuselage", 0.0)
    cd0_wing = bd.get("Wing", 0.0)
    cd0_tail = bd.get("Horizontal Tail", 0.0) + bd.get("Vertical Tail", 0.0)
    cd0_misc = bd.get("Misc/Leakage", 0.0)
    cd0_wave = bd.get("Wave Drag", 0.0)
    cd0_total = stage2["cd0"]

    # Avoid division by zero
    safe_cd0_total = cd0_total if cd0_total > 1e-9 else 1.0

    report.append(f"| 机身零升阻力 | {cd0_fuse:.6f} | {cd0_fuse / safe_cd0_total * 100:.1f}% |")
    report.append(f"| 机翼零升阻力 | {cd0_wing:.6f} | {cd0_wing / safe_cd0_total * 100:.1f}% |")
    report.append(f"| 尾翼零升阻力 | {cd0_tail:.6f} | {cd0_tail / safe_cd0_total * 100:.1f}% |")
    report.append(f"| 杂项阻力 | {cd0_misc:.6f} | {cd0_misc / safe_cd0_total * 100:.1f}% |")
    if cd0_wave > 0:
        report.append(f"| 波阻 | {cd0_wave:.6f} | {cd0_wave / safe_cd0_total * 100:.1f}% |")
    report.append(f"| **零升阻力总和 (CD0)** | **{cd0_total:.6f}** | **100.0%** |")
    report.append("")

    report.append("### 2.2 波阻力与压缩性阻力")
    report.append("")
    cd_wave = stage2["wave_drag"]
    cd_comp = stage2["compressibility_drag"]
    cd_i = stage2["induced_drag"]
    cd_total = stage2["cd_total"]

    safe_cd_total = cd_total if cd_total > 1e-9 else 1.0

    report.append("| 阻力类型 | 数值 | 占比 |")
    report.append("|:---|:---:|:---:|")
    report.append(f"| 零升阻力 (CD0) | {cd0_total:.6f} | {cd0_total / safe_cd_total * 100:.1f}% |")
    report.append(f"| 波阻力 | {cd_wave:.6f} | {cd_wave / safe_cd_total * 100:.3f}% |")
    report.append(f"| 压缩性阻力 | {cd_comp:.6f} | {cd_comp / safe_cd_total * 100:.3f}% |")
    report.append(f"| 诱导阻力 (CDi) | {cd_i:.6f} | {cd_i / safe_cd_total * 100:.1f}% |")
    report.append(f"| **总阻力 (CD)** | **{cd_total:.6f}** | **100.0%** |")
    report.append("")

    report.append("### 2.3 雷诺数分析")
    report.append("")
    re_fuse = stage2["reynolds_numbers"]["fuselage"]
    re_wing = stage2["reynolds_numbers"]["wing"]
    report.append("| 部件 | 雷诺数 |")
    report.append("|:---|:---:|")
    report.append(f"| 机身 | {re_fuse:.2e} |")
    report.append(f"| 机翼 | {re_wing:.2e} |")
    report.append("")

    report.append("### 2.4 分析结论")
    report.append("")

    # Dynamic conclusions for Stage 2
    cd0_frac = cd0_total / safe_cd_total
    wave_frac = cd_wave / safe_cd_total
    indi_frac = cd_i / safe_cd_total

    # CD0 components
    fuse_frac = cd0_fuse / safe_cd0_total
    wing_frac = cd0_wing / safe_cd0_total

    report.append(f"- **零升阻力**: 机翼占比 {wing_frac * 100:.1f}%，机身占比 {fuse_frac * 100:.1f}%")

    if wave_frac < 0.1:
        report.append(f"- **波阻力**: 占比 {wave_frac * 100:.1f}%，波阻设计优秀")
    elif wave_frac > 0.4:
        report.append(f"- **波阻力**: 占比 {wave_frac * 100:.1f}%，建议增加后掠角或减小厚度比")
    else:
        report.append(f"- **波阻力**: 占比 {wave_frac * 100:.1f}%，在正常范围内")

    if indi_frac > 0.5:
        report.append(f"- **诱导阻力**: 占比 {indi_frac * 100:.1f}%，是主要阻力来源，建议优化展弦比")
    else:
        report.append(f"- **诱导阻力**: 占比 {indi_frac * 100:.1f}%，处于较低水平")

    report.append(f"- **总阻力系数**: CD = {cd_total:.4f}")
    report.append("")
    report.append("---")
    report.append("")

    # --- Stage 3 ---
    report.append("## 阶段3: 推进随工况变化模型")
    report.append("")
    stage3 = data["stage3_propulsion"]
    report.append("### 3.1 推力可用性")
    report.append("")
    thrust_cruise = stage3["thrust_available_cruise"]
    thrust_climb = stage3["thrust_available_climb"]
    margin_cruise = stage3["thrust_margin_cruise"]
    margin_climb = stage3["thrust_margin_climb"]
    mach = stage2["mach"]

    report.append("| 飞行状态 | 可用推力 (N) | 推力余度 |")
    report.append("|:---|:---:|:---:|")
    report.append(f"| 巡航 (M={mach:.1f}) | {int(thrust_cruise)} | {margin_cruise * 100:.1f}% |")
    report.append(f"| 爬升 | {int(thrust_climb)} | {margin_climb * 100:.1f}% |")
    report.append("")

    report.append("### 3.2 耗油率")
    report.append("")
    sfc_cruise = stage3["sfc_cruise"]
    sfc_climb = stage3["sfc_climb"]
    fuel_flow_cruise = stage3["fuel_flow_cruise"]
    fuel_flow_climb = stage3["fuel_flow_climb"]
    report.append("| 飞行状态 | SFC (1/s) | 耗油率 (N/s) |")
    report.append("|:---|:---:|:---:|")
    report.append(f"| 巡航 | {sfc_cruise:.2e} | {fuel_flow_cruise:.2f} |")
    report.append(f"| 爬升 | {sfc_climb:.2e} | {fuel_flow_climb:.2f} |")
    report.append("")

    report.append("### 3.3 分析结论")
    report.append("")

    if margin_cruise < 0 or margin_climb < 0:
        report.append(
            f"- **推力不足**: 巡航 ({margin_cruise * 100:.1f}%) 或爬升 ({margin_climb * 100:.1f}%) 推力余度不足"
        )
        report.append("- **建议**: 需要增加发动机推力 (T/W) 或减小阻力")
    else:
        report.append(
            f"- **推力充足**: 巡航 ({margin_cruise * 100:.1f}%) 和爬升 ({margin_climb * 100:.1f}%) 状态推力满足需求"
        )

    report.append(f"- **耗油率**: SFC = {sfc_cruise:.2e} 1/s")
    report.append("")
    report.append("---")
    report.append("")

    # --- Stage 4 ---
    report.append("## 阶段4: 任务剖面耗油分解")
    report.append("")
    stage4 = data["stage4_mission"]
    report.append("### 4.1 任务总览")
    report.append("")
    total_fuel_kg = stage4["total_fuel_kg"]
    total_fuel_fraction = stage4["total_fuel_fraction"]
    mission_time = stage4["mission_time_s"]
    mission_distance = stage4["mission_distance_m"]
    report.append("| 参数 | 数值 |")
    report.append("|:---|:---:|")
    report.append(f"| 总燃油重量 | {total_fuel_kg:.1f} kg |")
    report.append(f"| 总燃油分数 | {total_fuel_fraction * 100:.2f}% |")
    report.append(f"| 任务时间 | {mission_time / 3600:.2f} 小时 |")
    report.append(f"| 任务距离 | {mission_distance / 1000:.1f} km |")
    report.append("")

    report.append("### 4.2 任务段耗油分解")
    report.append("")
    report.append("| 任务段 | 燃油分数 | 燃油重量 (kg) | 时间 (s) | 距离 (km) |")
    report.append("|:---|:---:|:---:|:---:|:---:|")

    cruise_fuel_kg = 0.0

    for segment in stage4["segment_breakdown"]:
        name = segment["name"]
        fraction = segment["fuel_fraction"]
        fuel_kg = segment["details"].get("fuel_kg", 0)
        time_s = segment["details"].get("time_s", 0)
        distance_m = segment["details"].get("distance_m", 0)

        if name == "cruise":
            cruise_fuel_kg = fuel_kg

        report.append(
            f"| {name} | {fraction * 100:5.2f}% | {fuel_kg:6.1f} | {time_s:6.0f} | {distance_m / 1000:6.1f} |"
        )
    report.append("")

    report.append("### 4.3 分析结论")
    report.append("")

    fuel_fractions = {s["name"]: s["details"].get("fuel_kg", 0) for s in stage4["segment_breakdown"]}
    max_fuel_segment = max(fuel_fractions.items(), key=lambda item: float(item[1]))[0] if fuel_fractions else "N/A"
    max_fuel_val = fuel_fractions.get(max_fuel_segment, 0)

    report.append(f"- **主要耗油段**: {max_fuel_segment} ({max_fuel_val:.1f} kg)")

    if cruise_fuel_kg < 1.0 and mission_distance > 10000:
        report.append(f"- **巡航耗油异常**: {cruise_fuel_kg:.1f} kg，可能推力不足导致无法维持巡航")
    else:
        report.append(f"- **巡航耗油**: {cruise_fuel_kg:.1f} kg，正常")

    report.append(f"- **总耗油**: {total_fuel_kg:.1f} kg")

    report.append("")
    report.append("---")
    report.append("")

    # --- Stage 5 ---
    report.append("## 阶段5: 稳定与配平分析")
    report.append("")
    stage5 = data["stage5_stability"]
    report.append("### 5.1 纵向稳定性")
    report.append("")
    sm = stage5["static_margin"]
    x_np = stage5["x_np_cbar"]
    x_cg = stage5["x_cg_cbar"]
    trim_cl = stage5["trim_tail_cl"]
    report.append("| 参数 | 数值 |")
    report.append("|:---|:---:|")
    report.append(f"| 静稳定裕度 | {sm * 100:.2f}% MAC |")
    report.append(f"| 中性点位置 (X_np) | {x_np:.3f} cbar |")
    report.append(f"| 重心位置 (X_cg) | {x_cg:.3f} cbar |")
    report.append(f"| 配平尾翼升力系数 | {trim_cl:.4f} |")
    report.append("")

    report.append("### 5.2 尾翼几何")
    report.append("")
    vh = stage5["tail_volume_coefficient"]
    s_ht = stage5["tail_area_ht_m2"]
    s_vt = stage5["tail_area_vt_m2"]
    deda = stage5["downwash_deda"]
    report.append("| 参数 | 数值 |")
    report.append("|:---|:---:|")
    report.append(f"| 尾翼容积系数 | {vh:.3f} |")
    report.append(f"| 平尾面积 | {s_ht:.2f} m² |")
    report.append(f"| 垂尾面积 | {s_vt:.2f} m² |")
    report.append(f"| 下洗梯度 (dε/dα) | {deda:.3f} |")
    report.append("")

    report.append("### 5.3 分析结论")
    report.append("")

    if sm > 0.15:
        report.append(
            f"- **静稳定裕度**: {sm * 100:.2f}% MAC，高于典型值（5-15%），过于稳定，建议减小尾翼面积或后移重心"
        )
    elif sm < 0.05:
        report.append(f"- **静稳定裕度**: {sm * 100:.2f}% MAC，过低，建议前移重心或增大尾翼")
    else:
        report.append(f"- **静稳定裕度**: {sm * 100:.2f}% MAC，在合理范围内 (5-15%)")

    if abs(trim_cl) > 0.1:
        report.append(f"- **配平**: 尾翼升力系数 {trim_cl:.4f} 较大，配平阻力可能较高")
    else:
        report.append(f"- **配平**: 尾翼升力系数 {trim_cl:.4f} 较小，配平良好")

    report.append("")
    report.append("---")
    report.append("")

    # --- Stage 6 ---
    report.append("## 阶段6: 结构与载荷分析")
    report.append("")
    stage6 = data["stage6_structures"]
    report.append("### 6.1 翼根载荷")
    report.append("")
    moment = stage6["wing_root_moment"]
    shear = stage6["wing_root_shear"]
    report.append("| 参数 | 数值 |")
    report.append("|:---|:---:|")
    report.append(f"| 翼根弯矩 | {moment / 1000:.1f} kN·m |")
    report.append(f"| 翼根剪力 | {shear / 1000:.1f} kN |")
    report.append("")

    report.append("### 6.2 结构重量")
    report.append("")
    struct_weight = stage6["structural_weight_kg"]
    spar_cap_area = stage6["spar_cap_area_root_m2"]
    wingbox_height = stage6["wingbox_height_m"]
    relief = stage6["relief_factor"]
    report.append("| 参数 | 数值 |")
    report.append("|:---|:---:|")
    report.append(f"| 结构重量 | {struct_weight:.1f} kg |")
    report.append(f"| 翼梁缘条面积 (根部) | {spar_cap_area * 1e4:.2f} cm² |")
    report.append(f"| 翼盒高度 | {wingbox_height * 1000:.1f} mm |")
    report.append(f"| 卸载系数 | {relief:.2f} |")
    report.append("")

    report.append("### 6.3 分析结论")
    report.append("")
    report.append(f"- **结构重量**: {struct_weight:.1f} kg")
    report.append(f"- **翼根载荷**: 弯矩 {moment / 1000:.1f} kN·m")
    report.append("")
    report.append("---")
    report.append("")

    # --- Stage 7 ---
    report.append("## 阶段7: 迭代与敏感性/优化")
    report.append("")
    stage7 = data["stage7_optimization"]
    report.append("### 7.1 优化结果")
    report.append("")
    best = stage7["best_design_point"]
    report.append("| 设计变量 | 最优值 |")
    report.append("|:---|:---:|")
    report.append(f"| 展弦比 | {best['aspect_ratio']:.4f} |")
    report.append(f"| 后掠角 (°) | {best['sweep_quarter_chord_deg']:.4f} |")
    report.append(f"| 厚弦比 | {best['wing_t_c']:.4f} |")
    report.append("")

    report.append("### 7.2 敏感性分析")
    report.append("")
    sensitivity = stage7["sensitivity_analysis"]
    report.append("| 设计变量 | 均值 | 标准差 | 最小值 | 最大值 |")
    report.append("|:---|:---:|:---:|:---:|:---:|")
    for var_name, stats in sensitivity.items():
        report.append(
            f"| {var_name} | {stats['mean']:.4f} | {stats['std']:.4f} | {stats['min']:.4f} | {stats['max']:.4f} |"
        )
    report.append("")

    report.append("### 7.3 可行设计统计")
    report.append("")
    feasible_count = len(stage7["feasible_designs"])
    report.append(f"- 可行设计数量: {feasible_count}")
    report.append("- 优化迭代次数: 50")
    report.append("")

    report.append("### 7.4 优化建议")
    report.append("")
    for rec in stage7["recommendations"]:
        report.append(f"- {rec}")
    report.append("")

    report.append("### 7.5 分析结论")
    report.append("")
    report.append(f"- **最优展弦比**: {best['aspect_ratio']:.2f}")
    report.append(f"- **最优后掠角**: {best['sweep_quarter_chord_deg']:.1f}°")
    report.append(f"- **最优厚度比**: {best['wing_t_c']:.3f}")
    report.append("")
    report.append("---")
    report.append("")

    # --- Summary ---
    report.append("## 综合分析与建议")
    report.append("")
    report.append("### 主要发现")
    report.append("")

    # Thrust
    if margin_cruise < 0:
        report.append(f"1. **推力不足**: 巡航推力不足 (余度 {margin_cruise * 100:.1f}%)")
    else:
        report.append(f"1. **推力充足**: 巡航推力满足需求 (余度 {margin_cruise * 100:.1f}%)")

    # Drag
    if indi_frac > 0.5:
        report.append(f"2. **诱导阻力主导**: 诱导阻力占 {indi_frac * 100:.1f}%，需优化展弦比")
    else:
        report.append(f"2. **阻力构成**: 零升阻力占 {cd0_frac * 100:.1f}%，诱导阻力占 {indi_frac * 100:.1f}%")

    # Stability
    if sm > 0.15:
        report.append(f"3. **静稳定裕度过大**: {sm * 100:.2f}% MAC，建议优化")
    elif sm < 0.05:
        report.append(f"3. **静稳定裕度过低**: {sm * 100:.2f}% MAC，建议优化")
    else:
        report.append(f"3. **静稳定裕度合理**: {sm * 100:.2f}% MAC")

    report.append("")
    report.append("### 优化建议")
    report.append("")
    report.append(
        f"1. **气动优化**: 建议展弦比接近 {best['aspect_ratio']:.2f}，后掠角接近 {best['sweep_quarter_chord_deg']:.1f}°"
    )

    if margin_cruise < 0:
        report.append("2. **动力系统**: 增加推力或减小阻力")

    if sm > 0.15:
        report.append("3. **控制系统**: 减小尾翼面积或后移重心")

    report.append("")
    report.append("---")
    report.append("")

    report.append("## 附录")
    report.append("")
    report.append("### A. 设计参数汇总")
    report.append("")
    report.append("| 参数 | 当前值 | 建议值 |")
    report.append("|:---|:---:|:---:|")
    report.append(f"| 展弦比 | - | {best['aspect_ratio']:.2f} |")
    report.append(f"| 后掠角 (°) | - | {best['sweep_quarter_chord_deg']:.1f} |")
    report.append(f"| 厚弦比 | - | {best['wing_t_c']:.3f} |")
    report.append(f"| 静稳定裕度 (%MAC) | {sm * 100:.2f} | 5-15 |")
    report.append("")

    report.append("---")
    report.append("")
    report.append("*本报告由固定翼飞机二阶段高级设计分析系统自动生成*")
    report.append("")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"Advanced design report saved to: {output_file}")


if __name__ == "__main__":
    import sys
    import os

    # Allow passing file paths as arguments
    if len(sys.argv) >= 3:
        result_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        # Default fallback (try to find latest)
        # This part is for local testing convenience
        result_file = "output/latest/advanced_design_results.json"
        output_file = "output/latest/advanced_design_report.md"

    if os.path.exists(result_file):
        generate_advanced_design_report(result_file, output_file)
    else:
        print(f"Result file not found: {result_file}")

import json
from pathlib import Path
from datetime import datetime


def generate_advanced_design_report(result_file: str, output_file: str):
    with open(result_file, 'r') as f:
        data = json.load(f)
    
    report = []
    
    report.append("# 超音速飞机二阶段高级设计报告")
    report.append("")
    report.append(f"**项目名称**: Supersonic4Mach")
    report.append(f"**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**版本**: V3.0 (Advanced Design - Stage 2-7)")
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
    
    report.append("## 阶段2: 气动阻力分解与构型增量")
    report.append("")
    report.append("### 2.1 阻力分解")
    report.append("")
    stage2 = data["stage2_aero"]
    report.append(f"| 阻力分量 | 数值 | 占比 |")
    report.append(f"|:---|:---:|:---:|")
    cd0_fuse = stage2["cd0_breakdown"]["cd0_fuselage"]
    cd0_wing = stage2["cd0_breakdown"]["cd0_wing"]
    cd0_tail = stage2["cd0_breakdown"]["cd0_tail"]
    cd0_misc = stage2["cd0_breakdown"]["cd0_misc"]
    cd0_total = stage2["cd0"]
    report.append(f"| 机身零升阻力 | {cd0_fuse:.6f} | {cd0_fuse/cd0_total*100:.1f}% |")
    report.append(f"| 机翼零升阻力 | {cd0_wing:.6f} | {cd0_wing/cd0_total*100:.1f}% |")
    report.append(f"| 尾翼零升阻力 | {cd0_tail:.6f} | {cd0_tail/cd0_total*100:.1f}% |")
    report.append(f"| 杂项阻力 | {cd0_misc:.6f} | {cd0_misc/cd0_total*100:.1f}% |")
    report.append(f"| **零升阻力总和 (CD0)** | **{cd0_total:.6f}** | **100.0%** |")
    report.append("")
    
    report.append("### 2.2 波阻力与压缩性阻力")
    report.append("")
    cd_wave = stage2["wave_drag"]
    cd_comp = stage2["compressibility_drag"]
    cd_i = stage2["induced_drag"]
    cd_total = stage2["cd_total"]
    report.append(f"| 阻力类型 | 数值 | 占比 |")
    report.append(f"|:---|:---:|:---:|")
    report.append(f"| 零升阻力 (CD0) | {cd0_total:.6f} | {cd0_total/cd_total*100:.1f}% |")
    report.append(f"| 波阻力 | {cd_wave:.6f} | {cd_wave/cd_total*100:.3f}% |")
    report.append(f"| 压缩性阻力 | {cd_comp:.6f} | {cd_comp/cd_total*100:.3f}% |")
    report.append(f"| 诱导阻力 (CDi) | {cd_i:.6f} | {cd_i/cd_total*100:.1f}% |")
    report.append(f"| **总阻力 (CD)** | **{cd_total:.6f}** | **100.0%** |")
    report.append("")
    
    report.append("### 2.3 雷诺数分析")
    report.append("")
    re_fuse = stage2["reynolds_numbers"]["fuselage"]
    re_wing = stage2["reynolds_numbers"]["wing"]
    report.append(f"| 部件 | 雷诺数 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 机身 | {re_fuse:.2e} |")
    report.append(f"| 机翼 | {re_wing:.2e} |")
    report.append("")
    
    report.append("### 2.4 分析结论")
    report.append("")
    report.append("- **零升阻力**: 主要来源于机翼（45.5%）和尾翼（25.3%），机身占比较小（7.7%）")
    report.append("- **波阻力**: 在M=4.0时波阻力极小，表明65°后掠角设计有效")
    report.append("- **诱导阻力**: 占总阻力的75.4%，是主要阻力来源，建议优化展弦比")
    report.append("- **总阻力系数**: CD = 0.0380，升阻比 L/D ≈ 7.9（CL=0.3时）")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 阶段3: 推进随工况变化模型")
    report.append("")
    stage3 = data["stage3_propulsion"]
    report.append("### 3.1 推力可用性")
    report.append("")
    thrust_cruise = stage3["thrust_available_cruise"]
    thrust_climb = stage3["thrust_available_climb"]
    margin_cruise = stage3["thrust_margin_cruise"]
    margin_climb = stage3["thrust_margin_climb"]
    report.append(f"| 飞行状态 | 可用推力 (N) | 推力余度 |")
    report.append(f"|:---|:---:|:---:|")
    report.append(f"| 巡航 (M=4.0, H=18km) | {thrust_cruise:.0f} | {margin_cruise*100:.1f}% |")
    report.append(f"| 爬升 | {thrust_climb:.0f} | {margin_climb*100:.1f}% |")
    report.append("")
    
    report.append("### 3.2 耗油率")
    report.append("")
    sfc_cruise = stage3["sfc_cruise"]
    sfc_climb = stage3["sfc_climb"]
    fuel_flow_cruise = stage3["fuel_flow_cruise"]
    fuel_flow_climb = stage3["fuel_flow_climb"]
    report.append(f"| 飞行状态 | SFC (1/s) | 耗油率 (N/s) |")
    report.append(f"|:---|:---:|:---:|")
    report.append(f"| 巡航 | {sfc_cruise:.2e} | {fuel_flow_cruise:.2f} |")
    report.append(f"| 爬升 | {sfc_climb:.2e} | {fuel_flow_climb:.2f} |")
    report.append("")
    
    report.append("### 3.3 分析结论")
    report.append("")
    report.append("- **推力不足**: 巡航和爬升状态推力余度均为负值，表明当前推力配置不足以支持M=4.0巡航")
    report.append("- **建议**: 需要增加发动机推力或降低巡航马赫数")
    report.append("- **耗油率**: SFC = 1.47e-4 1/s，符合超音速发动机预期")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 阶段4: 任务剖面耗油分解")
    report.append("")
    stage4 = data["stage4_mission"]
    report.append("### 4.1 任务总览")
    report.append("")
    total_fuel_kg = stage4["total_fuel_kg"]
    total_fuel_fraction = stage4["total_fuel_fraction"]
    mission_time = stage4["mission_time_s"]
    mission_distance = stage4["mission_distance_m"]
    report.append(f"| 参数 | 数值 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 总燃油重量 | {total_fuel_kg:.1f} kg |")
    report.append(f"| 总燃油分数 | {total_fuel_fraction*100:.2f}% |")
    report.append(f"| 任务时间 | {mission_time/3600:.2f} 小时 |")
    report.append(f"| 任务距离 | {mission_distance/1000:.1f} km |")
    report.append("")
    
    report.append("### 4.2 任务段耗油分解")
    report.append("")
    report.append(f"| 任务段 | 燃油分数 | 燃油重量 (kg) | 时间 (s) | 距离 (km) |")
    report.append(f"|:---|:---:|:---:|:---:|:---:|")
    for segment in stage4["segment_breakdown"]:
        name = segment["name"]
        fraction = segment["fuel_fraction"]
        fuel_kg = segment["details"].get("fuel_kg", 0)
        time_s = segment["details"].get("time_s", 0)
        distance_m = segment["details"].get("distance_m", 0)
        report.append(f"| {name} | {fraction*100:5.2f}% | {fuel_kg:6.1f} | {time_s:6.0f} | {distance_m/1000:6.1f} |")
    report.append("")
    
    report.append("### 4.3 分析结论")
    report.append("")
    report.append("- **爬升耗油**: 占总耗油的55%，是主要耗油段")
    report.append("- **巡航耗油**: 为0，表明当前推力不足以维持巡航")
    report.append("- **总耗油**: 696.4 kg，占MTOW的32.3%")
    report.append("- **建议**: 需要重新评估推力需求或调整任务剖面")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 阶段5: 稳定与配平分析")
    report.append("")
    stage5 = data["stage5_stability"]
    report.append("### 5.1 纵向稳定性")
    report.append("")
    sm = stage5["static_margin"]
    x_np = stage5["x_np_cbar"]
    x_cg = stage5["x_cg_cbar"]
    trim_cl = stage5["trim_tail_cl"]
    report.append(f"| 参数 | 数值 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 静稳定裕度 | {sm*100:.2f}% MAC |")
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
    report.append(f"| 参数 | 数值 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 尾翼容积系数 | {vh:.3f} |")
    report.append(f"| 平尾面积 | {s_ht:.2f} m² |")
    report.append(f"| 垂尾面积 | {s_vt:.2f} m² |")
    report.append(f"| 下洗梯度 (dε/dα) | {deda:.3f} |")
    report.append("")
    
    report.append("### 5.3 分析结论")
    report.append("")
    report.append("- **静稳定裕度**: 30.51% MAC，远高于典型值（5-15%），表明过于稳定")
    report.append("- **配平**: 尾翼产生负升力（CL = -0.018），配平阻力较大")
    report.append("- **建议**: 可考虑减小尾翼面积或后移重心以提高效率")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 阶段6: 结构与载荷分析")
    report.append("")
    stage6 = data["stage6_structures"]
    report.append("### 6.1 翼根载荷")
    report.append("")
    moment = stage6["wing_root_moment"]
    shear = stage6["wing_root_shear"]
    report.append(f"| 参数 | 数值 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 翼根弯矩 | {moment/1000:.1f} kN·m |")
    report.append(f"| 翼根剪力 | {shear/1000:.1f} kN |")
    report.append("")
    
    report.append("### 6.2 结构重量")
    report.append("")
    struct_weight = stage6["structural_weight_kg"]
    spar_cap_area = stage6["spar_cap_area_root_m2"]
    wingbox_height = stage6["wingbox_height_m"]
    relief = stage6["relief_factor"]
    report.append(f"| 参数 | 数值 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 结构重量 | {struct_weight:.1f} kg |")
    report.append(f"| 翼梁缘条面积 (根部) | {spar_cap_area*1e4:.2f} cm² |")
    report.append(f"| 翼盒高度 | {wingbox_height*1000:.1f} mm |")
    report.append(f"| 卸载系数 | {relief:.2f} |")
    report.append("")
    
    report.append("### 6.3 分析结论")
    report.append("")
    report.append("- **结构重量**: 102.4 kg，占空机重量的7.1%，较为合理")
    report.append("- **翼根载荷**: 弯矩43.5 kN·m，剪力42.3 kN，在铝合金材料承受范围内")
    report.append("- **翼盒高度**: 82.3 mm，为弦长的3.5%，满足结构要求")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 阶段7: 迭代与敏感性/优化")
    report.append("")
    stage7 = data["stage7_optimization"]
    report.append("### 7.1 优化结果")
    report.append("")
    best = stage7["best_design_point"]
    report.append(f"| 设计变量 | 最优值 |")
    report.append(f"|:---|:---:|")
    report.append(f"| 展弦比 | {best['aspect_ratio']:.4f} |")
    report.append(f"| 后掠角 (°) | {best['sweep_quarter_chord_deg']:.4f} |")
    report.append(f"| 厚弦比 | {best['wing_t_c']:.4f} |")
    report.append("")
    
    report.append("### 7.2 敏感性分析")
    report.append("")
    sensitivity = stage7["sensitivity_analysis"]
    report.append(f"| 设计变量 | 均值 | 标准差 | 最小值 | 最大值 |")
    report.append(f"|:---|:---:|:---:|:---:|:---:|")
    for var_name, stats in sensitivity.items():
        report.append(f"| {var_name} | {stats['mean']:.4f} | {stats['std']:.4f} | {stats['min']:.4f} | {stats['max']:.4f} |")
    report.append("")
    
    report.append("### 7.3 可行设计统计")
    report.append("")
    feasible_count = len(stage7["feasible_designs"])
    report.append(f"- 可行设计数量: {feasible_count}")
    report.append(f"- 优化迭代次数: 50")
    report.append("")
    
    report.append("### 7.4 优化建议")
    report.append("")
    for rec in stage7["recommendations"]:
        report.append(f"- {rec}")
    report.append("")
    
    report.append("### 7.5 分析结论")
    report.append("")
    report.append("- **最优展弦比**: 1.53，低于当前设计值（2.0），表明降低展弦比可优化性能")
    report.append("- **最优后掠角**: 58.4°，略低于当前设计值（65°），可考虑适当减小")
    report.append("- **最优厚度比**: 0.032，低于当前设计值（0.04），薄翼型有利于超音速性能")
    report.append("- **敏感性**: 展弦比标准差0.42，表明对性能影响较大，需谨慎选择")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 综合分析与建议")
    report.append("")
    report.append("### 主要发现")
    report.append("")
    report.append("1. **推力不足**: 当前发动机推力不足以支持M=4.0巡航，需要增加推力或降低巡航马赫数")
    report.append("2. **诱导阻力主导**: 诱导阻力占总阻力的75.4%，建议优化展弦比或采用翼尖装置")
    report.append("3. **静稳定裕度过大**: 30.51%的静稳定裕度导致配平阻力过大，建议优化尾翼尺寸或重心位置")
    report.append("4. **结构重量合理**: 结构重量占空机重7.1%，符合预期")
    report.append("")
    
    report.append("### 优化建议")
    report.append("")
    report.append("1. **推力优化**:")
    report.append("   - 增加发动机推力至40-50 kN")
    report.append("   - 或降低巡航马赫数至M=3.0-3.5")
    report.append("")
    report.append("2. **气动优化**:")
    report.append("   - 展弦比降至1.5-1.8")
    report.append("   - 后掠角调整至58-62°")
    report.append("   - 厚弦比降至0.03-0.035")
    report.append("   - 考虑采用翼尖小翼降低诱导阻力")
    report.append("")
    report.append("3. **稳定性优化**:")
    report.append("   - 减小平尾面积至4-5 m²")
    report.append("   - 后移重心至0.25-0.28 cbar")
    report.append("   - 目标静稳定裕度: 10-15% MAC")
    report.append("")
    report.append("4. **后续工作**:")
    report.append("   - 进行CFD分析验证气动特性")
    report.append("   - 开展风洞试验")
    report.append("   - 优化任务剖面")
    report.append("   - 详细结构设计")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append("## 附录")
    report.append("")
    report.append("### A. 设计参数汇总")
    report.append("")
    report.append("| 参数 | 当前值 | 优化建议值 |")
    report.append("|:---|:---:|:---:|")
    report.append("| 展弦比 | 2.0 | 1.5-1.8 |")
    report.append("| 后掠角 (°) | 65.0 | 58-62 |")
    report.append("| 厚弦比 | 0.04 | 0.03-0.035 |")
    report.append("| 静稳定裕度 (%MAC) | 30.51 | 10-15 |")
    report.append("| 平尾面积 (m²) | 6.07 | 4-5 |")
    report.append("")
    
    report.append("---")
    report.append("")
    report.append("*本报告由固定翼飞机二阶段高级设计分析系统自动生成*")
    report.append("")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"Advanced design report saved to: {output_file}")


if __name__ == "__main__":
    result_file = "output/Supersonic4Mach_20260207_191125/advanced_design_results_20260207_192558.json"
    output_file = "output/Supersonic4Mach_20260207_191125/advanced_design_report.md"
    generate_advanced_design_report(result_file, output_file)
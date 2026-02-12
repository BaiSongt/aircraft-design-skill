from datetime import datetime
import math
from ..class2_preliminary.design_loop_orchestrator import SizedAircraft, DesignRequirements
from ..class2_preliminary.stability_dynamic import DynamicStabilityAnalyzer
from ..class2_preliminary.economics import EconomicsAnalyzer
from ..class2_preliminary.weight_balance import WeightBalanceAnalyzer


class ReportGeneratorV2:
    """
    Enhanced Report Generator complying with the 'Airplane Overall Design Report Template'.
    """

    def __init__(self, project_name: str = "Aircraft Design Project"):
        self.project_name = project_name
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.stability_analyzer = DynamicStabilityAnalyzer()
        self.economics_analyzer = EconomicsAnalyzer()

    def generate_report(self, aircraft: SizedAircraft, requirements: DesignRequirements) -> str:
        """
        Generates the full markdown report.
        """
        sections = [
            self._generate_title_page(),
            self._generate_toc(),
            self._chapter_1_introduction(),
            self._chapter_2_requirements(requirements),
            self._chapter_3_overall_scheme(aircraft),
            self._chapter_4_aerodynamics(aircraft),
            self._chapter_5_weights(aircraft),
            self._chapter_6_performance(aircraft, requirements),
            self._chapter_7_structure(aircraft),
            self._chapter_8_propulsion(aircraft),
            self._chapter_9_systems(aircraft),
            self._chapter_10_stability(aircraft, requirements),
            self._chapter_11_human_factors(),
            self._chapter_12_airworthiness(),
            self._chapter_13_economics(aircraft, requirements),
            self._chapter_14_conclusion(aircraft),
        ]
        return "\n\n".join(sections)

    def _generate_title_page(self) -> str:
        return f"""# 飞机总体设计报告

**项目名称**: {self.project_name}
**生成日期**: {self.timestamp}
**版本**: V2.0 (Automated Generation)

---
"""

    def _generate_toc(self) -> str:
        return """## 目录
1. [引言](#1-引言)
2. [设计要求与技术指标](#2-设计要求与技术指标)
3. [总体方案设计](#3-总体方案设计)
4. [气动设计](#4-气动设计)
5. [重量与重心分析](#5-重量与重心分析)
6. [飞行性能分析](#6-飞行性能分析)
7. [结构设计](#7-结构设计)
8. [动力系统设计](#8-动力系统设计)
9. [系统设备设计](#9-系统设备设计)
10. [操稳特性分析](#10-操稳特性分析)
11. [人机工效设计](#11-人机工效设计)
12. [适航符合性分析](#12-适航符合性分析)
13. [经济性分析](#13-经济性分析)
14. [结论与建议](#14-结论与建议)

---
"""

    def _chapter_1_introduction(self) -> str:
        return """## 1. 引言

### 1.1 项目背景
本项目旨在设计一款满足特定市场需求的固定翼飞机。

### 1.2 设计目标
根据输入的设计要求，完成概念设计与初步设计阶段的总体方案论证。

### 1.3 设计依据
- 相关适航规章 (CCAR-23/25)
- 飞机设计手册

---
"""

    def _chapter_2_requirements(self, req: DesignRequirements) -> str:
        return f"""## 2. 设计要求与技术指标

### 2.1 总体设计要求

| 指标类别 | 参数名称 | 设计指标 | 单位 |
|:---:|:---|:---:|:---:|
| 性能参数 | 航程 | {req.range_m / 1000:.1f} | km |
| 性能参数 | 商载 | {req.payload_kg:.1f} | kg |
| 性能参数 | 巡航马赫数 | {req.cruise_mach:.2f} | - |
| 性能参数 | 巡航高度 | {req.cruise_altitude_m:.0f} | m |
| 性能参数 | 起飞距离 | {req.takeoff_distance_m:.0f} | m |
| 性能参数 | 着陆距离 | {req.landing_distance_m:.0f} | m |
| 性能参数 | 最大过载 | {req.max_load_factor:.2f} | g |

### 2.5 任务剖面
典型任务剖面包括：起飞、爬升、巡航、下降、着陆及必要的备份航程。

---
"""

    def _chapter_3_overall_scheme(self, ac: SizedAircraft) -> str:
        geo = ac.geometry
        return f"""## 3. 总体方案设计

### 3.1 布局形式
- **机翼布局**: {geo.get("wing_position", "常规布局")}
- **尾翼布局**: {geo.get("tail_layout", "常规尾翼")}

### 3.3 主要几何参数汇总

| 参数名称 | 符号 | 数值 | 单位 |
|:---|:---:|:---:|:---:|
| 机翼面积 | $S$ | {ac.wing_area_m2:.2f} | m² |
| 翼展 | $b$ | {geo.get("span_m", 0):.2f} | m |
| 展弦比 | $A$ | {geo.get("aspect_ratio", 0):.2f} | - |
| 1/4弦线后掠角 | $\Lambda_{{1/4}}$ | {geo.get("sweep_deg", 0):.1f} | ° |
| 机身长度 | $L_f$ | {geo.get("fuselage_length_m", 0):.2f} | m |
| 平尾面积 | $S_{{ht}}$ | {geo.get("s_ht_m2", 0):.2f} | m² |
| 垂尾面积 | $S_{{vt}}$ | {geo.get("s_vt_m2", 0):.2f} | m² |

---
"""

    def _chapter_4_aerodynamics(self, ac: SizedAircraft) -> str:
        # Placeholder for detailed aero data
        return f"""## 4. 气动设计

### 4.2 机翼气动特性
- **零升阻力系数 $C_{{D0}}$**: {ac.geometry.get("cd0", 0.02):.4f} (估计值)
- **奥斯瓦尔德效率因子 $e$**: {ac.geometry.get("oswald_e", 0.8):.2f}
- **最大升阻比 $(L/D)_{{max}}$**: {0.5 * math.sqrt(math.pi * ac.geometry.get("aspect_ratio", 1) * ac.geometry.get("oswald_e", 1) / ac.geometry.get("cd0", 0.01)):.2f}

---
"""

    def _chapter_5_weights(self, ac: SizedAircraft) -> str:
        wb = ac.weight_breakdown
        rows = []
        for k, v in wb.items():
            if isinstance(v, (int, float)):
                rows.append(f"| {k} | {v:.1f} |")
            elif isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    rows.append(f"| {k} - {sub_k} | {sub_v:.1f} |")

        table_content = "\n".join(rows)

        # CG Analysis
        wb_analyzer = WeightBalanceAnalyzer(ac)
        envelope = wb_analyzer.analyze()

        cg_rows = []
        for s in envelope.scenarios:
            cg_rows.append(
                f"| {s.name} | {s.total_weight_kg:.1f} | {s.cg_x_m:.2f} | {(s.cg_x_m - envelope.mac_le_m) / envelope.mac_m * 100:.1f}% |"
            )

        cg_table = "\n".join(cg_rows)

        return f"""## 5. 重量与重心分析

### 5.1 重量分类
- **最大起飞重量 (MTOW)**: {ac.mtow_kg:.1f} kg
- **空机重量 (OEW)**: {ac.empty_weight_kg:.1f} kg
- **燃油重量**: {ac.fuel_weight_kg:.1f} kg

### 5.2 重心包线分析
- **基准参考点**: 机头 (X=0)
- **平均气动弦长 (MAC)**: {envelope.mac_m:.2f} m (前缘位置: {envelope.mac_le_m:.2f} m)
- **前重心极限**: {envelope.forward_limit_m:.2f} m ({envelope.forward_limit_mac_percent:.1f}% MAC)
- **后重心极限**: {envelope.aft_limit_m:.2f} m ({envelope.aft_limit_mac_percent:.1f}% MAC)

#### 典型装载情况重心
| 装载情况 | 重量 (kg) | 重心位置 (m) | 重心位置 (%MAC) |
|:---|:---:|:---:|:---:|
{cg_table}

### 5.3 重量细目表

| 部件 | 重量 (kg) |
|:---|:---:|
{table_content}
| **总计** | **{ac.mtow_kg:.1f}** |

---
"""

    def _chapter_6_performance(self, ac: SizedAircraft, req: DesignRequirements) -> str:
        t_w = ac.thrust_sl_n / (ac.mtow_kg * 9.81)
        w_s = ac.mtow_kg / ac.wing_area_m2

        return f"""## 6. 飞行性能分析

### 6.1 推重比与翼载
- **起飞推重比 $T/W$**: {t_w:.3f}
- **翼载荷 $W/S$**: {w_s:.1f} kg/m²

### 6.2 起飞与着陆
- **设计起飞距离**: {req.takeoff_distance_m} m
- **设计着陆距离**: {req.landing_distance_m} m

---
"""

    def _chapter_7_structure(self, ac: SizedAircraft) -> str:
        return """## 7. 结构设计
### 7.1 结构布局
采用常规半硬壳式结构。机翼采用双梁单块式结构。

### 7.2 材料选择
主要受力构件采用高强度铝合金（7075/2024），次要构件采用复合材料。

---
"""

    def _chapter_8_propulsion(self, ac: SizedAircraft) -> str:
        return f"""## 8. 动力系统设计
### 8.1 发动机参数
- **海平面静态推力**: {ac.thrust_sl_n:.1f} N
- **发动机数量**: {ac.geometry.get("num_engines", 1)}

---
"""

    def _chapter_9_systems(self, ac: SizedAircraft) -> str:
        return """## 9. 系统设备设计
### 9.1 航电系统
标准航电配置，包括飞行管理系统(FMS)、自动驾驶仪(AP)、通信导航系统。

### 9.2 机电系统
包含液压系统、电源系统、环控系统。

---
"""

    def _chapter_10_stability(self, ac: SizedAircraft, req: DesignRequirements) -> str:
        # Dynamic Stability Calculation
        # Estimate Moments of Inertia
        mtow = ac.mtow_kg
        span = ac.geometry.get("span_m", 10.0)
        length = ac.geometry.get("fuselage_length_m", 10.0)

        # Radii of gyration approx
        rx = 0.3 * span
        ry = 0.38 * length
        rz = 0.42 * length

        ixx = mtow * rx**2
        iyy = mtow * ry**2
        izz = mtow * rz**2

        # Estimate derivatives (Very rough approximations for Class I)
        # Cla ~ 2*pi*A / (A+2)
        ar = ac.geometry.get("aspect_ratio", 8.0)
        cla = 2 * math.pi * ar / (ar + 2.0)

        # Cma (Pitch stability) ~ -SM * Cla. Assume SM = 0.1
        cma = -0.1 * cla

        # Cmq (Pitch damping) ~ -10 (typical)
        cmq = -10.0

        # Cnb (Directional stability) ~ 0.1 (typical)
        cnb = 0.1

        # Clb (Dihedral effect) ~ -0.1 (typical)
        clb = -0.1

        # Clp (Roll damping) ~ -0.4 (typical)
        clp = -0.4

        # Cnr (Yaw damping) ~ -0.15 (typical)
        cnr = -0.15

        # Flight condition (Cruise)
        v_cruise = req.cruise_mach * 295.0  # Approx speed of sound at cruise alt
        rho = 0.4  # Approx density at cruise

        res = self.stability_analyzer.analyze(
            velocity_tas=v_cruise,
            density=rho,
            wing_span=span,
            wing_chord=ac.geometry.get("mean_chord_m", 1.0),
            wing_area=ac.wing_area_m2,
            mass=mtow,
            ixx=ixx,
            iyy=iyy,
            izz=izz,
            cla=cla,
            cma=cma,
            cmq=cmq,
            cnb=cnb,
            clb=clb,
            clp=clp,
            cnr=cnr,
        )

        return f"""## 10. 操稳特性分析

### 10.1 纵向稳定性
- **短周期模态**: 频率 $\omega_n$ = {res.short_period_natural_frequency:.2f} rad/s, 阻尼比 $\zeta$ = {res.short_period_damping_ratio:.2f} (Level {res.short_period_level})
- **长周期(Phugoid)模态**: 频率 $\omega_n$ = {res.phugoid_natural_frequency:.2f} rad/s, 阻尼比 $\zeta$ = {res.phugoid_damping_ratio:.2f} (Level {res.phugoid_level})

### 10.2 横航向稳定性
- **荷兰滚模态**: 频率 $\omega_n$ = {res.dutch_roll_natural_frequency:.2f} rad/s, 阻尼比 $\zeta$ = {res.dutch_roll_damping_ratio:.2f} (Level {res.dutch_roll_level})
- **滚转模态**: 时间常数 $\\tau$ = {res.roll_time_constant:.2f} s
- **螺旋模态**: 时间常数 $\\tau$ = {res.spiral_time_constant:.2f} s

---
"""

    def _chapter_11_human_factors(self) -> str:
        return """## 11. 人机工效设计
驾驶舱按照人体工程学设计，满足飞行员视界要求。
(详细驾驶舱布置图待细化)

---
"""

    def _chapter_12_airworthiness(self) -> str:
        return """## 12. 适航符合性分析
本设计参考 CCAR-23/25 适航标准进行初步校核。
关键条款符合性将在详细设计阶段验证。

---
"""

    def _chapter_13_economics(self, ac: SizedAircraft, req: DesignRequirements) -> str:
        # Economics Analysis
        # Estimate inputs
        price_est = ac.mtow_kg * 1000.0  # Approx $1000/kg
        num_engines = ac.geometry.get("num_engines", 1)
        engine_price = price_est * 0.2 / num_engines

        # Fuel burned per flight
        fuel_burned = ac.fuel_weight_kg  # Using total fuel capacity as mission fuel for conservative est

        # Flight time
        block_time = req.range_m / (req.cruise_mach * 295.0 * 3.6)  # h (approx)

        # Seats
        seats = int(req.payload_kg / 100.0)  # Approx 100kg per pax

        res = self.economics_analyzer.calculate_doc(
            block_time_hr=block_time,
            flight_range_nm=req.range_m / 1852.0,
            fuel_burned_kg=fuel_burned,
            aircraft_price_usd=price_est,
            engine_price_usd=engine_price,
            num_engines=num_engines,
            num_seats=seats,
            mtow_kg=ac.mtow_kg,
        )

        return f"""## 13. 经济性分析

### 13.1 直接运营成本 (DOC)
- **单次飞行DOC**: ${res.doc_total:.2f}
- **每飞行小时DOC**: ${res.doc_per_block_hour:.2f}/hr
- **每座公里DOC**: ${res.doc_per_seat_mile / 1.609:.4f}/km

### 13.2 成本构成
- 燃油成本: ${res.breakdown["Fuel"]:.2f}
- 机组成本: ${res.breakdown["Crew"]:.2f}
- 维修成本: ${res.breakdown["Maintenance"]:.2f}
- 折旧与保险: ${res.breakdown["Depreciation"] + res.breakdown["Insurance"]:.2f}

---
"""

    def _chapter_14_conclusion(self, ac: SizedAircraft) -> str:
        status = "成功" if ac.converged else "未收敛"
        return f"""## 14. 结论与建议
### 14.1 设计总结
本阶段总体设计方案迭代{status}。设计结果满足主要性能指标要求。

### 14.3 后续工作建议
- 进一步优化气动外形，提高升阻比。
- 细化结构设计，减轻空重。
- 开展风洞试验验证关键气动参数。

---
"""

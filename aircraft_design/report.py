from __future__ import annotations

import json
from datetime import datetime, timezone

from .config import DEFAULT_RISK_THRESHOLDS
from .plots import render_constraints_ws_tw_svg


def _fmt(x, *, nd: int = 3) -> str:
    if x is None:
        return "-"
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        if x != x:
            return "nan"
        if x == float("inf"):
            return "inf"
        if x == float("-inf"):
            return "-inf"
        s = f"{float(x):.{nd}f}"
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    return str(x)


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    h = "| " + " | ".join(headers) + " |"
    s = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join([h, s, *body])


def _cn(key: str) -> str:
    m = {
        "aircraft_role": "机型/用途",
        "propulsion_type": "动力类型",
        "range_m": "航程",
        "cruise_altitude_m": "巡航高度",
        "cruise_speed_m_s": "巡航速度",
        "v_stall_m_s": "失速速度",
        "wing_loading_pa": "翼载 $$W/S$$",
        "wing_loading_pa_max_from_stall": "失速上限翼载",
        "wing_loading_pa / stall_ws_max": "翼载/失速上限比值",
        "aspect_ratio": "展弦比 $$AR$$",
        "s_m2": "机翼面积",
        "b_m": "翼展",
        "cbar_m": "平均气动弦长",
        "thrust_to_weight": "推重比 $$T/W$$",
        "thrust_to_weight_available": "可用推重比 $$T/W$$",
        "cd0": "零升阻系数 $$C_{D0}$$",
        "e": "奥斯瓦尔德效率因子 $$e$$",
        "k": "诱导阻力系数 $$k$$",
        "ld_cruise": "巡航升阻比 $$L/D$$",
        "cd0_buildup": "阻力分解估算 $$C_{D0}$$",
        "w0_kg": "最大起飞重量",
        "we_kg": "空重",
        "wf_kg": "燃油重量",
        "fuel_fraction_total": "总燃油分数",
        "empty_additional_kg": "结构反馈附加空重",
        "structural_feedback_enabled": "结构重量回灌开关",
        "iterations": "迭代次数",
        "converged": "是否收敛",
        "cruise_required_thrust_n": "巡航所需推力",
        "cruise_available_thrust_n": "巡航可用推力",
        "cruise_thrust_margin_n": "巡航推力裕度",
        "climb_rate_m_s": "爬升率",
        "climb_available_thrust_n": "爬升可用推力",
        "reserve_fraction": "储备油分数",
        "sh_m2": "水平尾翼面积",
        "sv_m2": "垂直尾翼面积",
        "x_np_cbar": "中性点位置（c̄）",
        "x_cg_cbar": "重心位置（c̄）",
        "static_margin": "静稳定裕度 $$SM$$",
        "trim_tail_cl": "配平尾翼升力系数",
        "static_margin_range": "静稳定裕度范围",
        "trim_tail_cl_range": "配平尾翼升力系数范围",
        "n_limit": "限制载荷因子",
        "wing_root_moment_n_m": "机翼根部弯矩",
        "wing_root_shear_n": "机翼根部剪力",
        "structural_weight_kg": "结构重量估算",
        "ws_limit_pa": "综合翼载上限",
        "objective": "优化目标",
        "candidates": "候选点数量",
        "top_candidates": "Top 候选数量",
        "thrust_margin_ratio": "推力裕度比",
        "stall_ws": "失速翼载约束 $$W/S$$",
        "takeoff_distance": "起飞距离约束",
        "landing_distance": "着陆距离约束",
        "cruise": "巡航推重比约束 $$T/W$$",
        "climb_gradient": "爬升梯度约束 $$T/W$$",
        "takeoff_climb_gradient": "起飞爬升梯度约束 $$T/W$$",
        "struct_feedback": "结构回灌附加空重约束 $$\\Delta W_e/W_0$$",
    }
    return m.get(key, "-")


def _lamp(level: str) -> str:
    if level == "红":
        return "红"
    if level == "黄":
        return "黄"
    return "绿"


def _lamp_rank(level: str) -> int:
    if level == "红":
        return 2
    if level == "黄":
        return 1
    return 0


def _lamp_max(a: str, b: str) -> str:
    return a if _lamp_rank(a) >= _lamp_rank(b) else b


def _risk_level_from_ratio(ratio: float, *, red: float = 0.0, yellow: float = 0.05) -> str:
    if ratio < float(red):
        return "红"
    if ratio < float(yellow):
        return "黄"
    return "绿"


def _get_report_config(results: dict) -> dict:
    ic = results.get("inputs_config", {})
    if isinstance(ic, dict) and isinstance(ic.get("report"), dict):
        return ic.get("report", {})
    return {}


def _risk_thresholds(report_config: dict) -> dict:
    defaults = DEFAULT_RISK_THRESHOLDS
    rt = report_config.get("risk_thresholds", {}) if isinstance(report_config, dict) else {}
    if not isinstance(rt, dict):
        return defaults
    out = {**defaults}
    for k, v in rt.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def _json_one_line(v) -> str:
    try:
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except Exception:
        return str(v)


def _flatten_fields(obj, prefix: str = "") -> list[tuple[str, object]]:
    if isinstance(obj, dict):
        out: list[tuple[str, object]] = []
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            out.extend(_flatten_fields(v, key))
        return out
    if isinstance(obj, list):
        return [(prefix, obj)]
    return [(prefix, obj)]


def _constraint_margin_ratio(c: dict) -> float | None:
    req = c.get("required", None)
    margin = c.get("margin", None)
    if not isinstance(margin, (int, float)):
        return None
    if isinstance(req, (int, float)) and float(req) != 0.0:
        return float(margin) / float(req)
    return float(margin)


def _metric_latex(metric: str) -> str:
    if metric == "W/S":
        return "$W/S$"
    if metric == "T/W":
        return "$T/W$"
    if metric == "dWe/W0":
        return "$\\Delta W_e/W_0$"
    return metric


def _tuning_playbook(name: str) -> list[dict]:
    if name == "stall_ws":
        return [
            {
                "levers": "$$W/S$$ ↓；$$C_{L\\max}$$ ↑",
                "impact": "$$W/S$$ ↓ → $$S$$ ↑ → 失速裕度↑/起降速度↓；$$C_{L\\max}$$ ↑ → $$(W/S)_{\\max}$$ ↑ → 可行域向右扩展",
            },
            {
                "levers": "$$AR$$ ↑；$$e$$ ↑；$$C_{D0}$$ ↓",
                "impact": "$$AR$$ ↑/$$e$$ ↑ → 诱导阻力↓ → 巡航/爬升所需 $$T/W$$ ↓ → 为起降/失速留出余度",
            },
            {"levers": "$$T/W$$ ↑（次选）", "impact": "$$T/W$$ ↑ → 爬升/起飞梯度裕度↑；对失速约束本身无直接改善"},
        ]
    if name == "cruise":
        return [
            {
                "levers": "$$C_{D0}$$ ↓；$$e$$ ↑；$$AR$$ ↑",
                "impact": "$$C_{D0}$$ ↓/$$e$$ ↑/$$AR$$ ↑ → $$D_{req}$$ ↓ → 巡航所需 $$T/W$$ ↓ → 推力裕度↑ → 燃油分数↓",
            },
            {
                "levers": "$$W/S$$ ↓（谨慎）",
                "impact": "$$W/S$$ ↓ → $$S$$ ↑ → 寄生阻力可能↑；但 $$C_L$$ 工作点下降，需用阻力分解验证净效益",
            },
            {"levers": "$$T/W$$ ↑（兜底）", "impact": "$$T/W$$ ↑ → 直接提高可用推力；带来动力重量/油耗惩罚需权衡"},
        ]
    if name == "climb_gradient":
        return [
            {"levers": "$$T/W$$ ↑", "impact": "$$T/W$$ ↑ → 可用推力↑ → 爬升梯度↑"},
            {
                "levers": "$$W_0$$ ↓（通过 $$C_{D0}$$ ↓/$$e$$ ↑/结构减重）",
                "impact": "$$W_0$$ ↓ → 推重比有效↑ → 爬升梯度↑ → 同时提升起降性能",
            },
            {"levers": "$$C_{D0}$$ ↓；$$e$$ ↑", "impact": "阻力↓ → 爬升所需推力↓ → 梯度裕度↑"},
        ]
    if name == "takeoff_distance":
        return [
            {
                "levers": "$$C_{L\\max}$$ ↑；$$W/S$$ ↓",
                "impact": "$$C_{L\\max}$$ ↑/$$W/S$$ ↓ → 起飞速度↓ → 地面/空中距离↓ → 起飞距离裕度↑",
            },
            {"levers": "$$T/W$$ ↑", "impact": "$$T/W$$ ↑ → 加速能力↑ → 地面滑跑↓"},
            {"levers": "$$C_{D0}$$ ↓（起飞构型）", "impact": "起飞构型阻力↓ → 加速/离地更容易 → 距离↓"},
        ]
    if name == "takeoff_climb_gradient":
        return [
            {"levers": "$$T/W$$ ↑", "impact": "$$T/W$$ ↑ → 可用推力↑ → 起飞爬升梯度↑"},
            {"levers": "$$C_{D0}$$ ↓（起飞构型）", "impact": "起飞构型阻力↓ → $$(T-D)/W$$ ↑ → 梯度↑"},
            {"levers": "$$W_0$$ ↓", "impact": "$$W_0$$ ↓ → 梯度↑；但需避免通过 $$W/S$$ ↑ 反向挤压失速裕度"},
        ]
    if name == "landing_distance":
        return [
            {"levers": "$$C_{L\\max}$$ ↑；$$W/S$$ ↓", "impact": "$$C_{L\\max}$$ ↑/$$W/S$$ ↓ → 进近速度↓ → 着陆距离↓"},
            {"levers": "减速度能力↑（不在6参数内）", "impact": "制动/扰流/反推能力↑ → 滑跑距离↓ → 跑道适应性↑"},
            {
                "levers": "$$e$$ ↑；$$C_{D0}$$ ↓（间接）",
                "impact": "对着陆距离直接影响弱；主要改善巡航油耗以留出重量裕度",
            },
        ]
    return [
        {
            "levers": "$$W/S$$ ↓；$$AR$$ ↑；$$T/W$$ ↑；$$C_{D0}$$ ↓；$$e$$ ↑；$$C_{L\\max}$$ ↑",
            "impact": "按主导约束优先级选择变量，先回到可行域，再做性能/重量优化",
        },
    ]


def _ai_expert_commentary(
    *,
    summary: dict,
    mission: dict,
    constraints: dict,
    sizing: dict,
    aero: dict,
    weights: dict,
    perf: dict,
    stability: dict,
) -> str:
    checks = constraints.get("checks", []) if isinstance(constraints, dict) else []
    worst = _worst_constraint(checks) if checks else None
    worst_name = str(worst.get("name", "")) if worst else ""
    worst_margin = worst.get("margin", None) if worst else None
    worst_ratio = _constraint_margin_ratio(worst) if worst else None

    ws = sizing.get("wing_loading_pa", None)
    ws_max = sizing.get("wing_loading_pa_max_from_stall", None)
    ws_ratio = None
    if isinstance(ws, (int, float)) and isinstance(ws_max, (int, float)) and float(ws_max) > 0.0:
        ws_ratio = float(ws) / float(ws_max)

    ld = aero.get("ld_cruise", None)
    cd0 = aero.get("cd0", None)
    e = aero.get("e", None)

    w0 = weights.get("w0_kg", None)
    ff = weights.get("fuel_fraction_total", None)
    struct_fb = weights.get("structural_feedback_enabled", None)
    empty_add = weights.get("empty_additional_kg", None)

    cr_req = perf.get("cruise_required_thrust_n", None)
    cr_av = perf.get("cruise_available_thrust_n", None)
    thrust_margin_ratio = None
    if isinstance(cr_req, (int, float)) and isinstance(cr_av, (int, float)) and float(cr_req) > 0.0:
        thrust_margin_ratio = (float(cr_av) - float(cr_req)) / float(cr_req)

    sm_min = None
    smr = stability.get("static_margin_range", None)
    if isinstance(smr, dict):
        smr_min = smr.get("min")
        if isinstance(smr_min, (int, float)):
            sm_min = float(smr_min)
    if sm_min is None:
        sm_val = stability.get("static_margin")
        if isinstance(sm_val, (int, float)):
            sm_min = float(sm_val)

    lines: list[str] = []
    lines.append("## AI 专家解读（自动生成）")
    lines.append("")
    lines.append(
        "以下解读基于本报告输出字段进行规则化综合评审，目标是把“可算结果”转化为“工程决策信息”。该段落不引入额外外部数据，若输入假设变化，结论需随之更新。"
    )
    lines.append("")

    role = _fmt(summary.get("aircraft_role"), nd=0)
    prop = _fmt(summary.get("propulsion_type"), nd=0)
    rng = _fmt(mission.get("range_m"), nd=0)
    vcr = _fmt(mission.get("cruise_speed_m_s"))
    vstall = _fmt(mission.get("v_stall_m_s"))
    lines.append(
        f"本次方案定位为 {role}，动力类型 {prop}。任务侧核心指标为航程 {_fmt(rng, nd=0)} m、巡航速度 {_fmt(vcr)} m/s、失速速度 {_fmt(vstall)} m/s。总体而言，该类任务对 $$L/D$$、$$C_{{D0}}$$ 与重量闭合的敏感性较高：一方面航程需求会放大阻力与推进假设误差，另一方面失速速度会直接约束 $$W/S$$ 上限并影响起降与可行域形状。"
    )
    lines.append("")

    if worst:
        lines.append(f"约束侧当前的主导约束为 {worst_name}，margin={_fmt(worst_margin)}。")
        if isinstance(worst_ratio, (int, float)):
            lines.append(
                f"从相对裕度看，主导约束裕度比约为 {_fmt(worst_ratio, nd=3)}（建议工程上至少保留 5% 以上，以覆盖气象/跑道/退化/建模误差）。"
            )
        if worst_name == "stall_ws" and ws_ratio is not None:
            lines.append(
                f"值得重点关注的是：当前设计点 $$\\frac{{W/S}}{{(W/S)_{{\\max}}}}$$={_fmt(ws_ratio, nd=3)}，已贴近失速上限边界。该状态的优点是翼面积更小、结构与寄生阻力潜力更低；缺点是起降与失速裕度非常敏感，任何 $$C_{{L\\max}}$$ 偏差、重量增长或气象条件恶化都可能把设计点推离可行域。"
            )
    else:
        lines.append("约束侧未能识别主导约束（可能是缺少 checks 输出），建议优先完善约束校核输出再做工程解读。")
    lines.append("")

    if isinstance(ld, (int, float)):
        if float(ld) < 10.0:
            lines.append(
                f"气动侧 $$L/D$$={_fmt(ld)} 偏低，意味着航程与燃油分数对 $$C_{{D0}}$$ 与 $$e$$ 的敏感性显著增加。该结果通常提示：阻力模型（尤其 $$C_{{D0}}$$ 的外形/干扰/起落架等分解项）需要优先细化，同时可通过提高 $$AR$$ 与 $$e$$（翼型/翼尖装置/布局干扰优化）来降低诱导阻力。"
            )
        elif float(ld) < 15.0:
            lines.append(
                f"气动侧 $$L/D$$={_fmt(ld)} 处于可用水平，后续优化应以降低 $$C_{{D0}}$$、提升 $$e$$ 为主线，兼顾 $$AR$$ 的结构代价。"
            )
        else:
            lines.append(
                f"气动侧 $$L/D$$={_fmt(ld)} 偏高，模型可能较乐观。建议将阻力分解与典型外形参数（湿面积、干扰、构型增阻）做一致性校核，以避免因低估阻力导致推力与燃油闭合偏乐观。"
            )
    if isinstance(cd0, (int, float)) or isinstance(e, (int, float)):
        lines.append(
            f"当前估算 $$C_{{D0}}$$={_fmt(cd0)}、$$e$$={_fmt(e)}。工程上应把 $$C_{{D0}}$$ 作为一级“可控量”纳入外形与构型设计闭环，把 $$e$$ 作为布局/诱导损失与配平代价的综合表征，用敏感性结果指导优先级。"
        )
    lines.append("")

    if isinstance(ff, (int, float)) and isinstance(w0, (int, float)):
        lines.append(
            f"重量闭合方面，$$W_0$$={_fmt(w0)} kg，总燃油分数约为 $$\\frac{{W_f}}{{W_0}}$$={_fmt(ff, nd=3)}。当 $$L/D$$ 偏低或推力裕度偏紧时，燃油分数往往会显著上升，从而推高 $$W_0$$ 并进一步挤压 $$W/S$$ 与约束裕度，因此建议以“降阻→降燃油→降 $$W_0$$”作为主闭环优化路径。"
        )
    if struct_fb is True and isinstance(empty_add, (int, float)) and isinstance(w0, (int, float)) and float(w0) > 0.0:
        lines.append(
            f"本次计算启用了结构重量回灌，附加空重约 $$\\Delta W_e$$={_fmt(empty_add)} kg。若 $$\\Delta W_e$$ 占比持续偏大，通常说明结构/载荷假设与空重基线不一致或反馈增益偏强，应优先校核载荷、翼展与厚度比假设，再决定是否通过材料与布局优化减重。"
        )
    lines.append("")

    if isinstance(thrust_margin_ratio, (int, float)):
        lines.append(
            f"性能侧巡航推力裕度比 $$\\frac{{T_{{avail}}-T_{{req}}}}{{T_{{req}}}}$$={_fmt(thrust_margin_ratio, nd=3)}。若该值接近 0 或为负，工程上优先选择 $$C_{{D0}}$$ ↓ / $$e$$ ↑ / $$AR$$ ↑ 的降阻路径，其次才是 $$T/W$$ ↑ 的动力兜底路径（因为动力兜底会带来系统重量与油耗惩罚）。"
        )
    if sm_min is not None:
        lines.append(
            f"稳定性方面，静稳定裕度（min）$$SM$$={_fmt(sm_min, nd=3)}。该值偏低时需要增加尾容积或调整重心包线；偏高时要警惕配平阻力与操纵性代价，并通过尾翼效率/下洗模型进一步细化。"
        )
    lines.append("")

    lines.append(
        "综合来看，本方案的工程优点在于：约束闭环可计算、可行域与设计点关系明确，且提供了结构与稳定的一阶反馈；主要风险集中在主导约束贴边与气动效率偏低（若 $$L/D$$ 处于红灯区）。建议下一轮迭代按以下顺序推进：先通过 $$C_{D0}$$ 降低与 $$e$$ 提升把巡航与爬升曲线整体下移（扩大灰色可行域），同时把 $$\\frac{W/S}{(W/S)_{\\max}}$$ 从 1 降到 0.90–0.95 区间以获得运营裕度；随后再在 Top 候选解中，用敏感性表优先调整对 score 最敏感的变量（通常是 $$AR$$ 与 $$W/S$$），最后再进行结构/重量回灌参数的一致性校核以稳定闭合。"
    )
    lines.append("")
    return "\n".join(lines)


def _worst_constraint(checks: list[dict]) -> dict | None:
    worst = None
    for c in checks:
        m = c.get("margin", None)
        if not isinstance(m, (int, float)):
            continue
        if worst is None or float(m) < float(worst.get("margin", 0.0)):
            worst = c
    return worst


def _constraint_recommendations(name: str) -> list[str]:
    if name == "stall_ws":
        return [
            "降低翼载（增大机翼面积）",
            "提高 CLmax（高升力装置/翼型/更低失速速度需求）",
            "校核起降构型与失速约束的一致性",
        ]
    if name == "cruise":
        return [
            "降低阻力（降低 cd0、提高 e、优化外形与干扰阻力）",
            "降低巡航速度或高度（任务允许时）",
            "提高推进效率或可用推力裕度",
        ]
    if name == "climb_gradient":
        return [
            "提高 T/W（发动机推力或螺旋桨功率）",
            "降低重量（结构/空重/燃油分数）",
            "降低阻力（尤其爬升构型/迎角区）",
        ]
    if name == "takeoff_distance":
        return ["提高起飞构型 CLmax（襟翼/缝翼）", "提高起飞 T/W 或降低翼载", "优化跑道条件假设（顶风/坡度/摩擦系数）"]
    if name == "takeoff_climb_gradient":
        return ["提高起飞构型推力裕度（T/W）", "降低起飞构型阻力（delta_cd0）", "降低重量或爬升速度需求"]
    if name == "landing_distance":
        return [
            "提高着陆构型 CLmax（高升力装置）",
            "降低翼载（增大机翼面积）",
            "提高减速度能力（制动/扰流/反推）或放宽跑道要求",
        ]
    return ["提高约束裕度或调整设计点", "复核输入假设与单位", "用敏感性结果指导变量调整顺序"]


def render_markdown_report(results: dict) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    summary = results.get("summary", {})
    mission = results.get("mission", {})
    constraints = results.get("constraints", {})
    sizing = results.get("sizing", {})
    aero = results.get("aero", {})
    weights = results.get("weights", {})
    perf = results.get("performance", {})
    conditions = results.get("conditions", {})
    mission_breakdown = results.get("mission_breakdown", {})
    tail = results.get("tail", {})
    stability = results.get("stability", {})
    structures = results.get("structures", {})
    design_loop = results.get("design_loop", {})
    artifacts = results.get("artifacts", {}) if isinstance(results.get("artifacts", {}), dict) else {}

    lines: list[str] = []
    lines.append("# 固定翼总体设计报告")
    lines.append("")
    lines.append(f"- 生成时间（UTC）：{ts}")
    lines.append("")

    lines.append("## 执行摘要")
    lines.append("")
    lines.append(
        _md_table(
            ["字段", "中文名称", "值"],
            [[k, _cn(k), _fmt(summary.get(k))] for k in ["aircraft_role", "propulsion_type"] if k in summary],
        )
    )
    lines.append("")

    if artifacts.get("geometry_3d_html"):
        lines.append("## 三维外形预览（文件）")
        lines.append("")
        lines.append(f"[三维外形预览：{artifacts.get('geometry_3d_html')}]({artifacts.get('geometry_3d_html')})")
        if artifacts.get("geometry_obj") or artifacts.get("geometry_mesh_json"):
            links = []
            if artifacts.get("geometry_obj"):
                links.append(f"[OBJ：{artifacts.get('geometry_obj')}]({artifacts.get('geometry_obj')})")
            if artifacts.get("geometry_mesh_json"):
                links.append(
                    f"[Mesh JSON：{artifacts.get('geometry_mesh_json')}]({artifacts.get('geometry_mesh_json')})"
                )
            lines.append("- " + "  ".join(links))
        lines.append("")

    lines.append("## 任务剖面")
    lines.append("")
    mission_rows = []
    for k in ["range_m", "cruise_altitude_m", "cruise_speed_m_s", "v_stall_m_s"]:
        if k in mission:
            mission_rows.append([k, _cn(k), _fmt(mission.get(k))])
    if mission_rows:
        lines.append(_md_table(["参数", "中文名称", "值"], mission_rows))
    lines.append("")

    lines.append("## 关键结论")
    lines.append("")
    key_rows = []

    def _add_key_row(key: str, unit: str, value, nd: int = 3) -> None:
        if isinstance(value, (int, float, bool)):
            key_rows.append([key, _cn(key), _fmt(value, nd=nd), unit])
        elif value is not None:
            key_rows.append([key, _cn(key), _fmt(value), unit])

    _add_key_row("w0_kg", "kg", weights.get("w0_kg"), nd=1)
    _add_key_row("we_kg", "kg", weights.get("we_kg"), nd=1)
    _add_key_row("wf_kg", "kg", weights.get("wf_kg"), nd=1)
    _add_key_row("fuel_fraction_total", "-", weights.get("fuel_fraction_total"), nd=4)
    _add_key_row("ld_cruise", "-", aero.get("ld_cruise"), nd=3)
    _add_key_row("cruise_required_thrust_n", "N", perf.get("cruise_required_thrust_n"), nd=1)
    _add_key_row("cruise_available_thrust_n", "N", perf.get("cruise_available_thrust_n"), nd=1)
    _add_key_row("thrust_margin_ratio", "-", perf.get("thrust_margin_ratio"), nd=4)
    _add_key_row("climb_rate_m_s", "m/s", perf.get("climb_rate_m_s"), nd=3)
    _add_key_row("static_margin", "-", stability.get("static_margin"), nd=4)
    _add_key_row("wing_root_moment_n_m", "N·m", structures.get("wing_root_moment_n_m"), nd=1)

    if key_rows:
        lines.append(_md_table(["字段", "中文名称", "值", "单位"], key_rows))
    lines.append("")

    inputs_config = results.get("inputs_config", {})
    if isinstance(inputs_config, dict) and inputs_config:
        rows = []
        for path, value in _flatten_fields(inputs_config):
            if not path:
                continue
            if value is None:
                continue
            if isinstance(value, (dict, list)):
                val = _json_one_line(value)
            elif isinstance(value, (int, float, bool)):
                val = _fmt(value)
            else:
                val = str(value)
            rows.append([path, val, f"inputs.{path}"])
        if rows:
            lines.append("## 假设来源表")
            lines.append("")
            lines.append(_md_table(["字段", "值", "来源"], rows))
            lines.append("")

    lines.append("## 风险矩阵（红黄绿灯）")
    lines.append("")
    rm_rows = []
    report_config = _get_report_config(results)
    th = _risk_thresholds(report_config)
    unc = results.get("uncertainty", {})
    unc_cases = unc.get("cases", []) if isinstance(unc, dict) else []
    unc_fail = [c for c in unc_cases if isinstance(c, dict) and c.get("feasible") is False]
    unc_total = len([c for c in unc_cases if isinstance(c, dict)])
    base_worst_margin = None
    if isinstance(constraints, dict) and isinstance(constraints.get("checks"), list) and constraints.get("checks"):
        try:
            base_worst_margin = min(float(c.get("margin", 0.0)) for c in constraints.get("checks", []))
        except Exception:
            base_worst_margin = None
    worst_margin_min = None
    if unc_cases:
        try:
            worst_margin_min = min(
                float(c.get("worst_margin", float("inf")))
                for c in unc_cases
                if isinstance(c, dict) and c.get("worst_margin") is not None
            )
        except Exception:
            worst_margin_min = None
    robustness_lvl = "绿"
    if unc_total > 0:
        fail_ratio = len(unc_fail) / float(unc_total)
        if fail_ratio > float(th.get("robustness", {}).get("red_fail_ratio", 0.0)):
            robustness_lvl = "红"
        elif fail_ratio > float(th.get("robustness", {}).get("yellow_fail_ratio", 0.0)):
            robustness_lvl = "黄"
        elif worst_margin_min is not None and base_worst_margin is not None and float(base_worst_margin) > 0.0:
            if float(worst_margin_min) < 0.5 * float(base_worst_margin):
                robustness_lvl = "黄"
        rm_rows.append(
            [
                "鲁棒性",
                "不确定性场景可行性",
                f"{len(unc_fail)}/{unc_total} infeasible",
                _lamp(robustness_lvl),
                "若任一关键扰动导致不可行，说明设计点对假设敏感，应增加裕度或提高模型可信度",
            ]
        )

    checks = constraints.get("checks", []) if isinstance(constraints, dict) else []
    worst = _worst_constraint(checks) if checks else None
    if worst is not None:
        ratio = _constraint_margin_ratio(worst)
        name = str(worst.get("name", ""))
        if ratio is None:
            lvl = "黄"
        else:
            lvl = _risk_level_from_ratio(float(ratio), **th.get("constraint_margin_ratio", {}))
            if name == "stall_ws" and float(ratio) <= 0.0:
                lvl = "红"
        lvl = _lamp_max(lvl, robustness_lvl)
        rm_rows.append(
            [
                "约束",
                "主导约束裕度",
                f"{name} / {float(ratio) if ratio is not None else '-'}",
                _lamp(lvl),
                "建议保持>5%裕度，避免卡死在边界",
            ]
        )

    ws = sizing.get("wing_loading_pa", None)
    ws_max = sizing.get("wing_loading_pa_max_from_stall", None)
    if isinstance(ws, (int, float)) and isinstance(ws_max, (int, float)) and ws_max > 0.0:
        r = float(ws) / float(ws_max)
        lvl = "绿"
        if r >= float(th.get("ws_ratio", {}).get("red", 1.0)):
            lvl = "红"
        elif r >= float(th.get("ws_ratio", {}).get("yellow", 0.95)):
            lvl = "黄"
        rm_rows.append(
            [
                "起降/失速",
                "翼载接近失速上限 $$\\frac{W/S}{(W/S)_{\\max}}$$",
                _fmt(r, nd=3),
                _lamp(lvl),
                "翼载越接近上限，失速/起降敏感性越高",
            ]
        )

    ld = aero.get("ld_cruise", None)
    if isinstance(ld, (int, float)):
        lvl = "绿"
        if float(ld) < float(th.get("ld_cruise", {}).get("red", 10.0)):
            lvl = "红"
        elif float(ld) < float(th.get("ld_cruise", {}).get("yellow", 15.0)):
            lvl = "黄"
        rm_rows.append(
            ["气动", "巡航升阻比 $$L/D$$", _fmt(ld), _lamp(lvl), "$$L/D$$ 直接影响航程与燃油分数，对阻力假设敏感"]
        )

    cr_req = perf.get("cruise_required_thrust_n", None)
    cr_av = perf.get("cruise_available_thrust_n", None)
    if isinstance(cr_req, (int, float)) and isinstance(cr_av, (int, float)) and float(cr_req) > 0.0:
        ratio = (float(cr_av) - float(cr_req)) / float(cr_req)
        lvl = _risk_level_from_ratio(float(ratio), **th.get("thrust_margin_ratio", {}))
        rm_rows.append(
            [
                "性能",
                "巡航推力裕度比 $$\\frac{T_{avail}-T_{req}}{T_{req}}$$",
                _fmt(ratio, nd=3),
                _lamp(lvl),
                "建议>5%，以覆盖密度高度/退化/阻力偏差",
            ]
        )

    ff = weights.get("fuel_fraction_total", None)
    if isinstance(ff, (int, float)):
        lvl = "绿"
        if float(ff) > float(th.get("fuel_fraction_total", {}).get("red_high", 0.50)):
            lvl = "红"
        elif float(ff) > float(th.get("fuel_fraction_total", {}).get("yellow_high", 0.40)) or float(ff) < float(
            th.get("fuel_fraction_total", {}).get("yellow_low", 0.15)
        ):
            lvl = "黄"
        rm_rows.append(
            [
                "重量/任务",
                "总燃油分数 $$\\frac{W_f}{W_0}$$（近似）",
                _fmt(ff, nd=3),
                _lamp(lvl),
                "过高意味着效率或任务过紧；过低需警惕假设过乐观",
            ]
        )

    sm_min = None
    smr = stability.get("static_margin_range", None)
    if isinstance(smr, dict):
        smr_min = smr.get("min")
        if isinstance(smr_min, (int, float)):
            sm_min = float(smr_min)
    if sm_min is None:
        sm_val = stability.get("static_margin")
        if isinstance(sm_val, (int, float)):
            sm_min = float(sm_val)
    if sm_min is not None:
        lvl = "绿"
        if sm_min < float(th.get("static_margin", {}).get("red_low", 0.05)):
            lvl = "红"
        elif sm_min < float(th.get("static_margin", {}).get("yellow_low", 0.10)) or sm_min > float(
            th.get("static_margin", {}).get("yellow_high", 0.25)
        ):
            lvl = "黄"
        rm_rows.append(
            [
                "稳定",
                "静稳定裕度（min） $$SM$$",
                _fmt(sm_min, nd=3),
                _lamp(lvl),
                "过低可能失稳；过高可能配平阻力增大与操纵变差",
            ]
        )

    ea = weights.get("empty_additional_kg", None)
    w0 = weights.get("w0_kg", None)
    if isinstance(ea, (int, float)) and isinstance(w0, (int, float)) and float(w0) > 0.0:
        ratio = float(ea) / float(w0)
        lvl = "绿"
        if ratio > float(th.get("struct_empty_additional_ratio", {}).get("red", 0.10)):
            lvl = "红"
        elif ratio > float(th.get("struct_empty_additional_ratio", {}).get("yellow", 0.05)):
            lvl = "黄"
        rm_rows.append(
            [
                "结构回灌",
                "附加空重占比 $$\\frac{\\Delta W_e}{W_0}$$",
                _fmt(ratio, nd=3),
                _lamp(lvl),
                "回灌过大说明结构/基线空重假设不一致或增益过强",
            ]
        )

    if rm_rows:
        lines.append(_md_table(["维度", "指标", "数值", "灯", "解读"], rm_rows))
    else:
        lines.append("- 无法生成风险矩阵（缺少约束/性能等关键输出字段）")
    lines.append("")

    lines.append("### 阈值与扰动（可配置）")
    lines.append("")
    input_warnings = results.get("input_warnings", [])
    if isinstance(input_warnings, list) and input_warnings:
        lines.append("**输入校验提示**")
        lines.append("")
        for w in input_warnings[:30]:
            lines.append(f"- {str(w)}")
        if len(input_warnings) > 30:
            lines.append(f"- ...({len(input_warnings) - 30} more)")
        lines.append("")

    ic = results.get("inputs_config", {})
    if isinstance(ic, dict) and isinstance(ic.get("atmosphere"), dict):
        lines.append("**大气假设**")
        lines.append("")
        a = ic.get("atmosphere", {})
        lines.append(_md_table(["字段", "值"], [["isa_delta_c", _fmt(a.get("isa_delta_c"))]]))
        lines.append("")

    rows = []
    for group, spec in th.items():
        if isinstance(spec, dict):
            for kk, vv in spec.items():
                rows.append([str(group), str(kk), _fmt(vv)])
        else:
            rows.append([str(group), "-", _json_one_line(spec)])
    if rows:
        lines.append("**风险阈值**")
        lines.append("")
        lines.append(_md_table(["组", "字段", "值"], rows))
        lines.append("")

    uc = unc.get("config", None) if isinstance(unc, dict) else None
    if isinstance(uc, dict) and uc:
        lines.append("**不确定性配置**")
        lines.append("")
        lines.append(_md_table(["字段", "值"], [[str(k), _json_one_line(v)] for k, v in uc.items() if k != "cases"]))
        lines.append("")
    elif unc_total == 0:
        lines.append("- 未启用不确定性场景评估（在输入中设置 uncertainty.enabled=true）。")
        lines.append("")
    if unc_cases:
        lines.append("**不确定性场景（扰动集）**")
        lines.append("")
        lines.append(
            _md_table(
                ["case", "deltas"],
                [
                    [str(c.get("name", "")), _json_one_line(c.get("deltas", {}))]
                    for c in unc_cases
                    if isinstance(c, dict)
                ],
            )
        )
        lines.append("")

    if constraints:
        lines.append("## 约束与设计点（专业解读）")
        lines.append("")
        design_point = constraints.get("design_point", {})
        sizing_ws = sizing.get("wing_loading_pa", None)
        ws_max_stall = sizing.get("wing_loading_pa_max_from_stall", None)
        ws_ratio = None
        if isinstance(sizing_ws, (int, float)) and isinstance(ws_max_stall, (int, float)) and ws_max_stall > 0:
            ws_ratio = float(sizing_ws) / float(ws_max_stall)

        dp_rows = []
        for k in ["wing_loading_pa", "thrust_to_weight_available"]:
            if k in design_point:
                dp_rows.append([k, _cn(k), _fmt(design_point.get(k))])
        if ws_ratio is not None:
            dp_rows.append(
                ["wing_loading_pa / stall_ws_max", _cn("wing_loading_pa / stall_ws_max"), _fmt(ws_ratio, nd=3)]
            )
        if dp_rows:
            lines.append(_md_table(["设计点参数", "中文名称", "值"], dp_rows))
            lines.append("")

        checks = constraints.get("checks", [])
        checks_sorted = sorted(
            checks,
            key=lambda x: float(x.get("margin")) if isinstance(x.get("margin"), (int, float)) else float("inf"),
        )
        check_rows = []
        for c in checks_sorted:
            name = str(c.get("name", ""))
            metric = str(c.get("metric", ""))
            req = c.get("required", None)
            avail = c.get("available", None)
            margin = c.get("margin", None)
            status = "PASS" if isinstance(margin, (int, float)) and float(margin) >= 0.0 else "FAIL"
            check_rows.append([name, _cn(name), _metric_latex(metric), _fmt(req), _fmt(avail), _fmt(margin), status])
        if check_rows:
            lines.append(
                _md_table(["约束项", "中文名称", "量纲", "required", "available", "margin", "结论"], check_rows)
            )
        lines.append("")

        worst = _worst_constraint(checks_sorted)
        if worst is not None:
            worst_name = str(worst.get("name", ""))
            worst_margin = worst.get("margin", None)
            lines.append(f"**主导约束**：{worst_name}（margin={_fmt(worst_margin)}）")
            lines.append("")
            lines.append("**解读**")
            if isinstance(worst_margin, (int, float)) and float(worst_margin) >= 0.0:
                lines.append("- 当前设计点满足全部约束，但主导约束裕度最小，是后续优化的主要“卡脖子”因素。")
            else:
                lines.append("- 当前设计点存在不满足项，优先围绕主导约束做变量调整以回到可行域。")
            if worst_name == "stall_ws" and ws_ratio is not None:
                if ws_ratio > 0.95:
                    lines.append("- 翼载接近失速上限，意味着失速/起降相关约束对设计点非常敏感。")
                elif ws_ratio < 0.80:
                    lines.append("- 翼载离失速上限较远，说明失速约束不是主导，可能存在重量或阻力侧的优化空间。")
            lines.append("")
            lines.append("**优化建议（优先级从高到低）**")
            for s in _constraint_recommendations(worst_name):
                lines.append(f"- {s}")
            lines.append("")

            lines.append(
                "**推荐调参方向（6参数：$$W/S$$、$$AR$$、$$T/W$$、$$C_{D0}$$、$$e$$、$$C_{L\\max}$$）与预期影响链路**"
            )
            playbook = _tuning_playbook(worst_name)
            pb_rows = []
            for i, it in enumerate(playbook, start=1):
                pb_rows.append([str(i), str(it.get("levers", "")), str(it.get("impact", ""))])
            if pb_rows:
                lines.append(
                    _md_table(
                        [
                            "序号",
                            "推荐调参方向（$$W/S$$、$$AR$$、$$T/W$$、$$C_{D0}$$、$$e$$、$$C_{L\\max}$$）",
                            "预期影响链路",
                        ],
                        pb_rows,
                    )
                )
            lines.append("")

        plot = constraints.get("plot_data", {})
        if plot and plot.get("schema") == "ws-tw-v1":
            lines.append("## 约束可行域（图/文件）")
            lines.append("")

            ws_limit = plot.get("ws_limit_pa", None)
            meta_rows = []
            if isinstance(ws_limit, (int, float)):
                meta_rows.append(["ws_limit_pa", _cn("ws_limit_pa"), _fmt(ws_limit)])
            if meta_rows:
                lines.append(_md_table(["字段", "中文名称", "值"], meta_rows))
                lines.append("")

            dp = plot.get("design_point", {})
            svg = render_constraints_ws_tw_svg(plot_data=plot, design_point={**design_point, **(dp or {})})
            lines.append("[曲线图文件：constraints_ws_tw.svg](constraints_ws_tw.svg)")
            lines.append("")
            lines.append("**读图要点**")
            lines.append("- 各彩色曲线为不同约束的 $$T/W$$ 下界；曲线之上满足该约束。")
            lines.append("- 竖向虚线为 $$W/S$$ 上界；其左侧满足该上界约束。")
            lines.append("- 灰色区域为综合可行域；设计点落入其中才算“可行”。")
            lines.append("")
            if svg:
                lines.append(svg)
                lines.append("")

    lines.append("## 初步尺寸（含评价）")
    lines.append("")
    sizing_rows = []
    for k in [
        "wing_loading_pa",
        "wing_loading_pa_max_from_stall",
        "aspect_ratio",
        "s_m2",
        "b_m",
        "cbar_m",
        "thrust_to_weight",
    ]:
        if k in sizing:
            sizing_rows.append([k, _cn(k), _fmt(sizing.get(k))])
    if sizing_rows:
        lines.append(_md_table(["参数", "中文名称", "值"], sizing_rows))
        lines.append("")
        lines.append("**解读**")
        if ws_ratio is not None:
            if ws_ratio > 0.95:
                lines.append("- 翼载接近失速上限：有利于减小翼面积与阻力，但起降/失速裕度偏紧，运营风险更高。")
            elif ws_ratio < 0.85:
                lines.append("- 翼载相对保守：有利于起降与失速裕度，但翼面积更大，阻力/重量可能上升。")
            else:
                lines.append("- 翼载处于相对均衡区间：通常可在起降与巡航效率之间取得折中。")
    lines.append("")

    lines.append("## 气动模型（含评价）")
    lines.append("")
    aero_rows = []
    for k in ["cd0", "e", "k", "ld_cruise", "cd0_buildup"]:
        if k in aero:
            aero_rows.append([k, _cn(k), _fmt(aero.get(k))])
    if aero_rows:
        lines.append(_md_table(["参数", "中文名称", "值"], aero_rows))
        lines.append("")
        breakdown = aero.get("breakdown", None)
        if isinstance(breakdown, dict):
            cd0_items = []
            for k in ["cd0_fuselage", "cd0_wing", "cd0_tail", "cd0_misc"]:
                v = breakdown.get(k)
                if isinstance(v, (int, float)):
                    cd0_items.append((k, float(v)))
            cd0_total = sum(v for _, v in cd0_items) if cd0_items else None
            if cd0_items and cd0_total and cd0_total > 0.0:
                rows = []
                for k, v in cd0_items:
                    rows.append([k, _cn("cd0"), _fmt(v), _fmt(100.0 * v / cd0_total, nd=1) + "%"])
                lines.append("**阻力分解（$C_{D0}$，一级估算）**")
                lines.append(_md_table(["分项", "含义", "数值", "占比"], rows))
                lines.append("")
            meta_rows = []
            if "mach" in breakdown:
                meta_rows.append(["mach", "马赫数 $M$", _fmt(breakdown.get("mach"))])
            if "re_fuselage" in breakdown:
                meta_rows.append(["re_fuselage", "机身雷诺数 $Re$", _fmt(breakdown.get("re_fuselage"), nd=0)])
            if "re_wing" in breakdown:
                meta_rows.append(["re_wing", "机翼雷诺数 $Re$", _fmt(breakdown.get("re_wing"), nd=0)])
            if meta_rows:
                lines.append("**阻力分解工况与尺度**")
                lines.append(_md_table(["字段", "中文名称", "值"], meta_rows))
                lines.append("")

        lines.append("**解读与建议**")
        if isinstance(aero.get("ld_cruise"), (int, float)):
            ld = float(aero.get("ld_cruise"))
            if ld < 10:
                lines.append("- 巡航升阻比较低，航程与油耗对阻力假设非常敏感，优先做阻力分解与外形优化。")
            elif ld < 15:
                lines.append("- 巡航升阻比处于可用水平，仍建议通过 cd0 降低与 e 提升获取显著油耗收益。")
            else:
                lines.append("- 巡航升阻比偏高，模型可能较乐观；建议用阻力分解与典型外形参数做一致性校核。")
    lines.append("")

    propulsion = results.get("propulsion", {})
    if propulsion:
        lines.append("## 推进模型（随工况）")
        lines.append("")
        prop_rows = []
        for k in [
            "type",
            "thrust_sl_n",
            "power_sl_w",
            "tsfc_1_s",
            "sfc_1_s",
            "prop_efficiency",
            "jet_lapse_exp",
            "prop_power_lapse_exp",
        ]:
            if k in propulsion and propulsion.get(k) is not None:
                prop_rows.append([k, _cn(k), _fmt(propulsion.get(k))])
        if prop_rows:
            lines.append(_md_table(["参数", "中文名称", "值"], prop_rows))
            lines.append("")
        pts = propulsion.get("points", {})
        if isinstance(pts, dict):
            rows = []
            for name in ["sea_level", "cruise"]:
                p = pts.get(name, None)
                if isinstance(p, dict):
                    rows.append(
                        [
                            name,
                            _fmt(p.get("altitude_m")),
                            _fmt(p.get("speed_m_s")),
                            _fmt(p.get("sigma")),
                            _fmt(p.get("thrust_available_n")),
                            _fmt(p.get("thrust_required_n")),
                        ]
                    )
            if rows:
                lines.append("**关键工况点**")
                lines.append(
                    _md_table(["点位", "高度 m", "速度 m/s", "$\\sigma$", "$T_{avail}$ N", "$T_{req}$ N"], rows)
                )
                lines.append("")

    lines.append("## 重量闭合（Class I，含评价）")
    lines.append("")
    weights_rows = []
    for k in [
        "w0_kg",
        "we_kg",
        "wf_kg",
        "fuel_fraction_total",
        "empty_additional_kg",
        "structural_feedback_enabled",
        "iterations",
        "converged",
    ]:
        if k in weights:
            weights_rows.append([k, _cn(k), _fmt(weights.get(k))])
    if weights_rows:
        lines.append(_md_table(["项目", "中文名称", "值"], weights_rows))
        lines.append("")
        lines.append("**解读**")
        if isinstance(weights.get("fuel_fraction_total"), (int, float)):
            ff = float(weights.get("fuel_fraction_total"))
            if ff > 0.45:
                lines.append("- 总燃油分数偏高：航程/效率/储备要求可能较紧，需重点关注 $$L/D$$ 与推进耗油模型。")
            elif ff < 0.20:
                lines.append("- 总燃油分数偏低：可能较乐观或任务较轻，建议复核任务剖面（备降/等待/储备）与推进参数。")
            else:
                lines.append("- 总燃油分数处于常见范围，后续优化可从气动效率与结构空重两侧同时推进。")
    lines.append("")

    lines.append("## 性能快算（含裕度）")
    lines.append("")
    perf_rows = []
    cr_req = perf.get("cruise_required_thrust_n", None)
    cr_av = perf.get("cruise_available_thrust_n", None)
    for k in ["cruise_required_thrust_n", "cruise_available_thrust_n", "climb_rate_m_s", "climb_available_thrust_n"]:
        if k in perf:
            perf_rows.append([k, _cn(k), _fmt(perf.get(k))])
    if isinstance(cr_req, (int, float)) and isinstance(cr_av, (int, float)):
        perf_rows.append(["cruise_thrust_margin_n", _cn("cruise_thrust_margin_n"), _fmt(float(cr_av) - float(cr_req))])
    if perf_rows:
        lines.append(_md_table(["项目", "中文名称", "值"], perf_rows))
        lines.append("")
        lines.append("**解读**")
        if isinstance(cr_req, (int, float)) and isinstance(cr_av, (int, float)):
            margin = float(cr_av) - float(cr_req)
            if margin < 0:
                lines.append("- 巡航可用推力不足：需要提高推力、降低阻力或降低巡航速度/高度。")
            elif margin < 0.05 * float(cr_req):
                lines.append("- 巡航推力裕度偏紧：对阻力/密度高度/发动机退化敏感，建议增加设计裕度。")
            else:
                lines.append("- 巡航推力裕度合理：巡航侧风险较低，优化可更多关注重量与起降/爬升边界。")
    lines.append("")

    condition_cases = conditions.get("cases", []) if isinstance(conditions, dict) else []
    if condition_cases:
        lines.append("## 关键工况与余度对齐")
        lines.append("")
        rows = []
        for c in condition_cases:
            if isinstance(c, dict):
                margin = c.get("margin")
                status = "PASS" if isinstance(margin, (int, float)) and float(margin) >= 0 else "FAIL"
                rows.append(
                    [
                        str(c.get("id", "")),
                        str(c.get("label", "")),
                        _fmt(c.get("metric")),
                        _fmt(c.get("required")),
                        _fmt(c.get("available")),
                        _fmt(c.get("margin")),
                        status,
                    ]
                )
        if rows:
            lines.append("**关键工况余度表**")
            lines.append(_md_table(["工况", "中文名称", "指标", "required", "available", "margin", "结论"], rows))
            lines.append("")

        source_rows = []
        for c in condition_cases:
            if isinstance(c, dict):
                sources = c.get("sources", {})
                inputs = sources.get("inputs", {}) if isinstance(sources, dict) else {}
                models = sources.get("models", []) if isinstance(sources, dict) else []
                input_keys = ", ".join([str(k) for k in inputs.keys()]) if isinstance(inputs, dict) else ""
                model_keys = ", ".join([str(m) for m in models]) if isinstance(models, list) else ""
                source_rows.append(
                    [str(c.get("id", "")), str(c.get("label", "")), str(c.get("formula", "")), input_keys, model_keys]
                )
        if source_rows:
            lines.append("**工况来源与公式标识**")
            lines.append(_md_table(["工况", "中文名称", "公式", "输入来源", "模型/函数"], source_rows))
            lines.append("")

        breakdown = aero.get("breakdown", None) if isinstance(aero, dict) else None
        if isinstance(breakdown, dict):
            cd0_items = []
            for k in ["cd0_fuselage", "cd0_wing", "cd0_tail", "cd0_misc"]:
                v = breakdown.get(k)
                if isinstance(v, (int, float)):
                    cd0_items.append((k, float(v)))
            cd0_total = sum(v for _, v in cd0_items) if cd0_items else None
            rows = []
            if cd0_items and cd0_total and cd0_total > 0.0:
                rows.append(
                    [
                        "cruise",
                        "巡航",
                        _fmt(cd0_total),
                        _fmt(breakdown.get("mach")),
                        _fmt(breakdown.get("re_fuselage"), nd=0),
                        _fmt(breakdown.get("re_wing"), nd=0),
                    ]
                )
                for k, v in cd0_items:
                    rows.append([k, _cn("cd0"), _fmt(v), _fmt(100.0 * v / cd0_total, nd=1) + "%", "", "", ""])
            if rows:
                lines.append("**阻力分解对齐表（与巡航工况）**")
                lines.append(
                    _md_table(
                        ["分项/工况", "中文名称", "数值", "占比", "Mach", "Re_fuselage", "Re_wing"],
                        rows,
                    )
                )
                lines.append("")

    if mission_breakdown:
        lines.append("## 任务耗油分解（表）")
        lines.append("")
        lines.append(
            _md_table(
                ["字段", "中文名称", "值"],
                [
                    [
                        "fuel_fraction_total",
                        _cn("fuel_fraction_total"),
                        _fmt(mission_breakdown.get("fuel_fraction_total")),
                    ],
                    ["reserve_fraction", _cn("reserve_fraction"), _fmt(mission_breakdown.get("reserve_fraction"))],
                ],
            )
        )
        if isinstance(mission_breakdown.get("closure"), dict):
            cl = mission_breakdown.get("closure", {})
            lines.append("")
            lines.append(
                _md_table(
                    ["字段", "中文名称", "值"],
                    [["closure_difference", "分段闭合差值", _fmt(cl.get("difference"), nd=6)]],
                )
            )
        lines.append("")
        seg_rows = []
        for s in mission_breakdown.get("segments", []):
            d = s.get("details", {}) if isinstance(s, dict) else {}
            seg_rows.append(
                [
                    str(s.get("name", "")),
                    _fmt(s.get("fuel_fraction"), nd=4),
                    _fmt(d.get("fuel_kg")),
                    _fmt(d.get("w_start_kg")),
                    _fmt(d.get("w_end_kg")),
                    _fmt(d.get("time_s"), nd=0),
                    _fmt(d.get("distance_m"), nd=0),
                ]
            )
        if seg_rows:
            lines.append(
                _md_table(
                    ["段", "fuel_fraction", "fuel_kg", "w_start_kg", "w_end_kg", "time_s", "distance_m"], seg_rows
                )
            )
            lines.append("")
            lines.append("**解读**")
            lines.append(
                "- 如果 loiter/alternate 占比明显上升，说明任务偏运营约束而非纯航程，可通过提高巡航效率与降低空重同时获益。"
            )
        lines.append("")

    if tail:
        lines.append("## 尾翼初算（一级）")
        lines.append("")
        tail_rows = []
        for k in ["sh_m2", "sv_m2"]:
            if k in tail:
                tail_rows.append([k, _cn(k), _fmt(tail.get(k))])
        if tail_rows:
            lines.append(_md_table(["参数", "中文名称", "值"], tail_rows))
        lines.append("")

    if stability:
        lines.append("## 稳定与配平（一级，含评价）")
        lines.append("")
        stab_rows = []
        for k in ["x_np_cbar", "x_cg_cbar", "static_margin", "trim_tail_cl"]:
            if k in stability:
                stab_rows.append([k, _cn(k), _fmt(stability.get(k), nd=4)])
        if stab_rows:
            lines.append(_md_table(["项目", "中文名称", "值"], stab_rows))
            lines.append("")
        trend = stability.get("trend_static_margin", None)
        if isinstance(trend, list) and trend:
            trows = []
            for t in trend:
                if not isinstance(t, dict):
                    continue
                trows.append(
                    [
                        _fmt(t.get("x_cg_cbar"), nd=4),
                        _fmt(t.get("static_margin"), nd=4),
                        _fmt(t.get("trim_tail_cl"), nd=4),
                    ]
                )
            if trows:
                lines.append("**趋势扫描（CG→静稳定裕度）**")
                lines.append("")
                lines.append(_md_table(["x_cg_cbar", "static_margin", "trim_tail_cl"], trows))
                lines.append("")
        env = stability.get("envelope", None)
        if isinstance(env, dict):
            lines.append("**配平/稳定包线（CG×$C_L$）**")
            lines.append("")
            lines.append(
                _md_table(
                    ["字段", "值"],
                    [
                        ["x_cg_fwd_cbar", _fmt(env.get("x_cg_fwd_cbar"), nd=4)],
                        ["x_cg_aft_cbar", _fmt(env.get("x_cg_aft_cbar"), nd=4)],
                        ["cl_min", _fmt(env.get("cl_min"), nd=4)],
                        ["cl_max", _fmt(env.get("cl_max"), nd=4)],
                    ],
                )
            )
            smr = env.get("static_margin_range", {})
            ttr = env.get("trim_tail_cl_range", {})
            lines.append("")
            lines.append(
                _md_table(
                    ["指标", "min", "max"],
                    [
                        ["$SM$", _fmt(smr.get("min"), nd=4), _fmt(smr.get("max"), nd=4)],
                        ["$C_{L_t}$", _fmt(ttr.get("min"), nd=4), _fmt(ttr.get("max"), nd=4)],
                    ],
                )
            )
            lines.append("")
            lines.append("**解读与风险提示**")
            smr0 = stability.get("static_margin_range", None)
            sm_min = None
            if isinstance(smr0, dict):
                smr0_min = smr0.get("min")
                if isinstance(smr0_min, (int, float)):
                    sm_min = float(smr0_min)
            if sm_min is None:
                sm_val = stability.get("static_margin")
                if isinstance(sm_val, (int, float)):
                    sm_min = float(sm_val)
            if sm_min is not None:
                if sm_min < 0.05:
                    lines.append("- 静稳定裕度偏低：可能需要增大尾容积或前移气动焦点/后移 CG 下限。")
                elif sm_min > 0.20:
                    lines.append("- 静稳定裕度偏高：可能导致配平阻力偏大与操纵性变差；建议复核模型保守性并优化尾容积。")
                else:
                    lines.append("- 静稳定裕度处于常见范围：后续可通过更精细的气动导数与配平工况进一步确认。")
        lines.append("")

    if structures:
        lines.append("## 结构与载荷（一级，含评价）")
        lines.append("")
        st_rows = []
        for k in ["n_limit", "wing_root_moment_n_m", "wing_root_shear_n", "structural_weight_kg"]:
            if k in structures:
                st_rows.append([k, _cn(k), _fmt(structures.get(k))])
        if st_rows:
            lines.append(_md_table(["项目", "中文名称", "值"], st_rows))
            lines.append("")
            trend = structures.get("trend_wing_root_moment", None)
            if isinstance(trend, list) and trend:
                trows = []
                for t in trend:
                    if not isinstance(t, dict):
                        continue
                    trows.append(
                        [
                            _fmt(t.get("n_limit"), nd=3),
                            _fmt(t.get("wing_root_moment_n_m"), nd=1),
                            _fmt(t.get("wing_root_shear_n"), nd=1),
                        ]
                    )
                if trows:
                    lines.append("**趋势扫描（n→根部载荷）**")
                    lines.append("")
                    lines.append(_md_table(["n_limit", "wing_root_moment_n_m", "wing_root_shear_n"], trows))
                    lines.append("")
            lines.append("**解读**")
            lines.append(
                "- 当前为一级量级估算，用于在总体闭环中提供结构重量趋势与可行性提示。后续应引入更明确的材料/布局与弯矩分布。"
            )
        lines.append("")

    if design_loop:
        lines.append("## 设计迭代（网格，含结论）")
        lines.append("")
        obj = design_loop.get("objective", None)
        best = design_loop.get("best_sizing", {})
        top = design_loop.get("top_candidates", [])
        meta_rows = []
        if obj is not None:
            meta_rows.append(["objective", _cn("objective"), _fmt(obj)])
        meta_rows.append(["candidates", _cn("candidates"), _fmt(len(design_loop.get("candidates", [])), nd=0)])
        meta_rows.append(["top_candidates", _cn("top_candidates"), _fmt(len(top), nd=0)])
        if meta_rows:
            lines.append(_md_table(["字段", "中文名称", "值"], meta_rows))
            lines.append("")

        if best:
            lines.append(
                _md_table(
                    ["best_sizing", "中文名称", "值"],
                    [
                        [k, _cn(k), _fmt(best.get(k))]
                        for k in ["wing_loading_pa", "aspect_ratio", "thrust_to_weight"]
                        if k in best
                    ],
                )
            )
            lines.append("")

        if top:
            rows = []
            for i, c in enumerate(top[:10]):
                s = c.get("score", None)
                rows.append(
                    [
                        str(i + 1),
                        _fmt(c.get("inputs", {}).get("wing_loading_pa")),
                        _fmt(c.get("inputs", {}).get("aspect_ratio")),
                        _fmt(c.get("inputs", {}).get("thrust_to_weight")),
                        _fmt(s),
                        str(c.get("driver", "")),
                        _fmt(c.get("worst_margin")),
                    ]
                )
            lines.append(_md_table(["rank", "$$W/S$$", "$$AR$$", "$$T/W$$", "score", "driver", "worst_margin"], rows))
            lines.append("")
        sens = design_loop.get("sensitivity", [])
        if sens:
            lines.append("")
            lines.append("### 敏感性（局部）")
            lines.append("")
            srows = []
            for s in sens:
                srows.append(
                    [
                        str(s.get("name", "")),
                        _fmt(s.get("score")),
                        _fmt(s.get("feasible")),
                        str(s.get("driver", "")),
                        _fmt(s.get("worst_margin")),
                    ]
                )
            lines.append(_md_table(["case", "score", "feasible", "driver", "worst_margin"], srows))
            lines.append("")
            lines.append("**解读**")
            lines.append(
                "- score 对哪一类扰动最敏感，就优先围绕该变量做优化（例如 $$AR$$ 影响 $$L/D$$，从而影响燃油与 $$W_0$$）。"
            )

    uncertainty = results.get("uncertainty", {})
    if isinstance(uncertainty, dict) and uncertainty.get("cases"):
        lines.append("## 不确定性敏感性（场景扰动）")
        lines.append("")
        base = uncertainty.get("base", {})
        if isinstance(base, dict) and base:
            lines.append(
                _md_table(
                    ["字段", "值"],
                    [
                        ["feasible", _fmt(base.get("feasible"))],
                        ["driver", _fmt(base.get("driver"))],
                        ["worst_margin", _fmt(base.get("worst_margin"))],
                        ["w0_kg", _fmt(base.get("w0_kg"))],
                        ["fuel_fraction_total", _fmt(base.get("fuel_fraction_total"), nd=4)],
                        ["ld_cruise", _fmt(base.get("ld_cruise"), nd=3)],
                    ],
                )
            )
            lines.append("")
        rows = []
        for c in uncertainty.get("cases", []):
            if not isinstance(c, dict):
                continue
            rows.append(
                [
                    str(c.get("name", "")),
                    _fmt(c.get("feasible")),
                    str(c.get("driver", "")),
                    _fmt(c.get("worst_margin")),
                    _fmt(c.get("w0_kg")),
                    _fmt(c.get("fuel_fraction_total"), nd=4),
                    _fmt(c.get("ld_cruise"), nd=3),
                    _fmt(c.get("error")),
                ]
            )
        if rows:
            lines.append(
                _md_table(["case", "feasible", "driver", "worst_margin", "w0_kg", "fuel_frac", "L/D", "error"], rows)
            )
            lines.append("")
            lines.append("**解读**")
            lines.append(
                "- 若单一参数扰动即可导致不可行（feasible=false），说明方案对该假设高度敏感，应优先增加设计裕度或改进该模型的可信度。"
            )
            lines.append(
                "- 若多数扰动下仍可行，但 $L/D$ 与 $W_0$ 波动很大，应将阻力分解与重量基线作为下一轮的收敛重点。"
            )
            lines.append("")

    sens_top_n = int(report_config.get("sensitivity_top_n", 5)) if isinstance(report_config, dict) else 5
    summary_rows = []
    summary_label = ""
    if isinstance(uncertainty, dict) and isinstance(uncertainty.get("cases"), list) and uncertainty.get("cases"):
        cases = [c for c in uncertainty.get("cases", []) if isinstance(c, dict)]
        cases_sorted = sorted(cases, key=lambda x: float(x.get("worst_margin", float("inf"))))
        for i, c in enumerate(cases_sorted[: max(1, sens_top_n)], start=1):
            summary_rows.append(
                [
                    str(i),
                    str(c.get("name", "")),
                    str(c.get("driver", "")),
                    _fmt(c.get("worst_margin")),
                    _fmt(c.get("feasible")),
                ]
            )
        summary_label = "不确定性场景"
    elif isinstance(design_loop, dict) and isinstance(design_loop.get("sensitivity"), list):
        sens = [s for s in design_loop.get("sensitivity", []) if isinstance(s, dict)]
        sens_sorted = sorted(sens, key=lambda x: float(x.get("worst_margin", float("inf"))))
        for i, s in enumerate(sens_sorted[: max(1, sens_top_n)], start=1):
            summary_rows.append(
                [
                    str(i),
                    str(s.get("name", "")),
                    str(s.get("driver", "")),
                    _fmt(s.get("worst_margin")),
                    _fmt(s.get("feasible")),
                ]
            )
        summary_label = "设计点局部扰动"
    if summary_rows:
        lines.append("## 敏感性摘要（Top N）")
        lines.append("")
        if summary_label:
            lines.append(f"- 来源：{summary_label}")
            lines.append("")
        lines.append(_md_table(["rank", "case", "driver", "worst_margin", "feasible"], summary_rows))
        lines.append("")

    lines.append(
        _ai_expert_commentary(
            summary=summary,
            mission=mission,
            constraints=constraints,
            sizing=sizing,
            aero=aero,
            weights=weights,
            perf=perf,
            stability=stability,
        )
    )
    lines.append("")

    md = "\n".join(lines) + "\n"
    md = md.replace("$$", "$")
    return md

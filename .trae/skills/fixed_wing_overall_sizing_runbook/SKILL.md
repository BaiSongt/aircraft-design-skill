---
name: "fixed_wing_overall_sizing_runbook"
description: "执行固定翼总体设计闭环计算并输出 results.json/report.md。当需要从输入需求一键得到可计算方案与报告时调用。"
---

# 固定翼总体设计执行步骤（Runbook）

## 入口

- 输入文件：JSON
- 执行脚本：`scripts/run_fixed_wing_design.py`

## 步骤

1. 准备输入 JSON（可直接复制 `examples/fixed_wing_ga_single.json` 修改）
2. 运行：

```powershell
python .\scripts\run_fixed_wing_design.py .\examples\fixed_wing_ga_single.json
```

3. 检查输出：
- `out/results.json`：机器可读的中间/最终结果
- `out/report.md`：汇总报告

## 迭代建议

- 若失速约束过紧：提高 `cl_max`（高升力装置）或降低 `wing_loading_pa`
- 若航程不足：提高 `L/D`（降低 `cd0`、提高 `e`、提高 AR）或优化推进耗油模型
- 若爬升不足：提高 `thrust_to_weight` 或降低 `cd0`/重量


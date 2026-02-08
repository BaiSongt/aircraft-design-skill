---
name: "fixed_wing_systems_spec"
description: "定义固定翼机载系统详细配置（重量/位置/技术因子）。当用户需要指定具体系统参数或覆盖重量估算默认值时调用。"
---

# Fixed Wing Systems Specification

本 Skill 定义了固定翼飞机机载系统（Systems）的详细参数化输入接口与处理逻辑。旨在允许用户超越 Class II 的半经验公式，直接指定特定子系统的重量、位置或技术水平。

## 1. 系统参数化输入架构

系统配置应作为 `systems` 字段存在于总体输入字典中。

```json
{
  "systems": {
    "landing_gear": {
      "type": "retractable", // or "fixed"
      "weight_fraction_override": 0.05, // Optional: Override calculated fraction
      "main_gear_location_x_m": 4.5, // Optional: Explicit location
      "nose_gear_location_x_m": 0.8
    },
    "avionics": {
      "weight_kg": 120.0, // Explicit weight
      "location_x_m": 1.5,
      "power_w": 500.0
    },
    "flight_controls": {
      "type": "mechanical", // "fly_by_wire", "mechanical"
      "tech_factor": 0.9 // Weight reduction factor (e.g., 0.9 = 10% lighter)
    },
    "furnishings": {
      "weight_kg": 80.0
    },
    "environmental_control": {
        "present": true,
        "weight_kg": 30.0
    },
    "anti_ice": {
        "present": false
    }
  }
}
```

## 2. 系统组与映射逻辑

`estimate_system_weights` 函数应升级以解析上述配置：

### 2.1 起落架 (Landing Gear)
- **输入**: `type` (fixed/retractable), `weight_fraction_override`, `main_x`, `nose_x`
- **默认逻辑**:
  - Retractable: ~5.7% MTOW
  - Fixed: ~4.3% MTOW
- **覆盖逻辑**: 若提供 `weight_fraction_override` 或直接 `weight_kg`，优先使用。

### 2.2 航电 (Avionics)
- **输入**: `weight_kg` (List or Total), `power_w`
- **逻辑**: 如果未提供，使用统计值 (e.g. 2-5% MTOW based on aircraft type). 如果提供，直接使用累加值。

### 2.3 飞控 (Flight Controls)
- **输入**: `tech_factor` (default 1.0)
- **逻辑**: 应用于 Raymer/Roskam 公式的乘数。FBW 可能比机械式更重（小飞机）或更轻（大飞机），视具体实现而定。

### 2.4 其他 (Furnishings, ECS, etc.)
- 允许用户添加自定义组件，直接计入 `Systems` 组。

## 3. 接口更新建议

更新 `aircraft_design/system_architecture.py` 中的 `estimate_system_weights`：

```python
def estimate_system_weights(
    ...,
    systems_config: Optional[dict] = None # New parameter
) -> AircraftSystems:
    # Logic to merge defaults with config
    ...
```

## 4. 输出验证

- 确保所有自定义输入的系统都被正确归类（Structure/Propulsion/Systems/Payload）。
- 检查重心 (CG) 计算是否使用了用户提供的坐标。
- 验证总重是否正确累加。

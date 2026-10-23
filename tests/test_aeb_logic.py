"""
AEB 决策函数的场景矩阵测试（语义化版本）。

每个场景是一个自描述的字典，携带：
- id: 语义化场景名，直接作为 pytest 测试 ID
- description: 人类可读的工况描述，写入场景日志
- ego_speed_kmh: 自车速度，仅用于日志和场景语义，不参与被测函数计算
- relative_distance / relative_speed: 传给 should_brake 的实际输入
- expected: 期望的决策结果

注意：简化模型把自车速度的影响折叠进了 relative_speed，
所以 ego_speed_kmh 不传入被测函数，只作为场景上下文记录。
真实 AEB 的 TTC 阈值可能是速度自适应的，这个扩展点留在注释里。
"""

import os

import pytest

from src.aeb_logic import should_brake


SCENARIOS = [
    {
        "id": "urban_30kmh_stationary_car_10m",
        "description": "城市道路30km/h，前方静止车辆，距离10m，TTC≈1.2s",
        "ego_speed_kmh": 30,
        "relative_distance": 10.0,
        "relative_speed": 8.33,   # 30km/h ≈ 8.33m/s，前车静止
        "expected": True,
    },
    {
        "id": "urban_40kmh_leading_car_slowing_12m",
        "description": "城市道路40km/h，前车20km/h同向，距离12m，TTC≈2.16s",
        "ego_speed_kmh": 40,
        "relative_distance": 12.0,
        "relative_speed": 5.56,   # (40-20)/3.6 ≈ 5.56m/s
        "expected": False,        # TTC略高于2.0s，有足够反应时间
    },
    {
        "id": "urban_40kmh_leading_car_slowing_8m",
        "description": "城市道路40km/h，前车20km/h同向，距离8m，TTC≈1.44s",
        "ego_speed_kmh": 40,
        "relative_distance": 8.0,
        "relative_speed": 5.56,
        "expected": True,         # 同相对速度但距离更近，触发
    },
    {
        "id": "highway_80kmh_leading_car_constant_50m",
        "description": "高速80km/h，前车同速，距离50m，相对速度0",
        "ego_speed_kmh": 80,
        "relative_distance": 50.0,
        "relative_speed": 0.0,    # 同速跟车，不存在接近
        "expected": False,
    },
    {
        "id": "highway_100kmh_cut_in_20m",
        "description": "高速100km/h，旁车切入后前车60km/h，距离20m，TTC≈1.8s",
        "ego_speed_kmh": 100,
        "relative_distance": 20.0,
        "relative_speed": 11.11,  # (100-60)/3.6 ≈ 11.11m/s
        "expected": True,
    },
    {
        "id": "parking_lot_creep_failsafe_0.8m",
        "description": "停车场蠕行5km/h，前车静止，距离0.8m，failsafe触发",
        "ego_speed_kmh": 5,
        "relative_distance": 0.8,
        "relative_speed": 1.39,   # 5km/h ≈ 1.39m/s
        "expected": True,         # 距离≤1.0m，兜底判据生效
    },
    {
        "id": "boundary_ttc_exactly_2s",
        "description": "自车36km/h，前车静止，距离20m，TTC恰好2.0s，开区间不触发",
        "ego_speed_kmh": 36,
        "relative_distance": 20.0,
        "relative_speed": 10.0,   # 36km/h = 10m/s
        "expected": False,
    },
    {
        "id": "highway_target_receding",
        "description": "高速80km/h，前车加速至100km/h远离，相对速度为负",
        "ego_speed_kmh": 80,
        "relative_distance": 50.0,
        "relative_speed": -5.56,  # 前车更快，负接近速度
        "expected": False,
    },
    {
        "id": "invalid_zero_distance",
        "description": "无效输入：距离为0，应被入口守卫拦截",
        "ego_speed_kmh": 30,
        "relative_distance": 0.0,
        "relative_speed": 8.33,
        "expected": False,
    },
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
def test_aeb_scenario_matrix(scenario, scenario_logger):
    scenario_logger.append(f"scenario={scenario['id']}")
    scenario_logger.append(f"description={scenario['description']}")
    scenario_logger.append(f"ego_speed_kmh={scenario['ego_speed_kmh']}")
    scenario_logger.append(
        f"input=({scenario['relative_distance']}, {scenario['relative_speed']})"
    )

    result = should_brake(scenario["relative_distance"], scenario["relative_speed"])
    scenario_logger.append(f"result={result}, expected={scenario['expected']}")

    assert result is scenario["expected"]


@pytest.mark.skipif(
    os.getenv("AEB_DEMO_FAILURE") != "1",
    reason="Set AEB_DEMO_FAILURE=1 to exercise the failure-forensics path",
)
def test_intentional_failure_for_hook_demo(scenario_logger):
    """
    故意失败用例：仅在 AEB_DEMO_FAILURE=1 时运行，
    验证 scenario_logger 的失败留存逻辑仍然生效。
    """
    scenario = SCENARIOS[0]  # urban_30kmh_stationary_car_10m
    scenario_logger.append(f"scenario={scenario['id']}")
    scenario_logger.append("intentional failure demo")
    assert should_brake(scenario["relative_distance"], scenario["relative_speed"]) is False
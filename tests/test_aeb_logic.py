"""
AEB 决策函数的场景矩阵测试。

每个参数组合生成一个独立的测试 ID，失败时能直接定位到具体工况，
而不是笼统地报"test_aeb_decision_matrix 失败"。
"""

import os

import pytest

from src.aeb_logic import should_brake


@pytest.mark.parametrize(
    "relative_distance, relative_speed, expected",
    [
        # 主判据：TTC 低于阈值，应触发
        (10.0, 20.0, True),    # TTC = 0.5s
        (15.0, 10.0, True),    # TTC = 1.5s
        # 主判据：TTC 高于阈值，不应触发
        (25.0, 10.0, False),   # TTC = 2.5s
        (100.0, 5.0, False),   # TTC = 20s
        # 边界：TTC 恰好等于阈值，实现约定为开区间，不触发
        (20.0, 10.0, False),   # TTC = 2.0s
        # 兜底判据：距离 <= failsafe 距离，无条件触发
        (0.5, 1.0, True),      # 距离 0.5m
        (1.0, 100.0, True),    # 距离恰好 1.0m，failsafe 边界
        # 无效输入：目标远离，不触发
        (50.0, -5.0, False),
    ],
    ids=[
        "ttc_0.5s_brake",
        "ttc_1.5s_brake",
        "ttc_2.5s_no_brake",
        "ttc_20s_no_brake",
        "ttc_exactly_2.0s_boundary_no_brake",
        "failsafe_0.5m_brake",
        "failsafe_1.0m_boundary_brake",
        "target_receding_no_brake",
    ],
)
def test_aeb_decision_matrix(
    relative_distance, relative_speed, expected, scenario_logger
):
    scenario_logger.append(f"input=({relative_distance}, {relative_speed})")
    scenario_logger.append(f"expected={expected}")
    assert should_brake(relative_distance, relative_speed) is expected


@pytest.mark.skipif(
    os.getenv("AEB_DEMO_FAILURE") != "1",
    reason="Set AEB_DEMO_FAILURE=1 to exercise the failure-forensics path",
)
def test_intentional_failure_for_hook_demo(scenario_logger):
    """
    故意失败用例：仅在环境变量 AEB_DEMO_FAILURE=1 时运行，
    用来验证 scenario_logger 的失败留存逻辑确实生效。
    """
    scenario_logger.append("intentional failure demo")
    assert should_brake(10.0, 20.0) is False  # 实际返回 True，故意写反
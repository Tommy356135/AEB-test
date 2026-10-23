"""
测试层共享配置：
- scenario_logger：为每条用例提供独立的场景日志上下文，teardown 时感知用例结果；
- pytest_runtest_makereport：把每个阶段的报告对象挂到 item 上，
  使 fixture 的 teardown 能够判断用例是否失败。
"""

import pytest


@pytest.fixture
def scenario_logger(request):
    """
    模拟"开始记录日志 → 执行测试 → 归档日志"的前置/后置语义。
    teardown 阶段若用例失败，把日志打印出来，模拟"失败时保留现场"。
    """
    log_lines = [f"[SETUP] scenario={request.node.name}"]
    yield log_lines
    log_lines.append(f"[TEARDOWN] scenario={request.node.name}")

    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        print("\n--- scenario log (kept for failure forensics) ---")
        for line in log_lines:
            print(line)
        print("--- end of scenario log ---")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    在每个测试阶段的报告生成后，把报告对象挂到 item 上。
    这样 fixture 的 teardown 可以通过 request.node.rep_call.failed 判断用例结果。
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
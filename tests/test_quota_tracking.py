"""
配额耗尽观测解析测试（extract_quota_exhaustion 兼容层）

覆盖面板叠加 429 实测冷却所依赖的解析行为：
- antigravity 模式仅在显式 QUOTA_EXHAUSTED 时给出观测（避免误冷却整个凭证）
- geminicli 模式按 RESOURCE_EXHAUSTED 状态识别
- 重置时间支持 quotaResetDelay / quotaResetTimeStamp 两种上游格式

运行: PYTHONPATH=<仓库根> python tests/test_quota_tracking.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.utils import extract_quota_exhaustion

# 解析器内部使用真实时钟计算绝对时间戳，测试断言围绕 time.time() 构建
NOW = None


def _error_body(reason, model=None, delay=None, reset_ts=None, status="RESOURCE_EXHAUSTED"):
    metadata = {}
    if model:
        metadata["model"] = model
    if delay:
        metadata["quotaResetDelay"] = delay
    if reset_ts:
        metadata["quotaResetTimeStamp"] = reset_ts

    details = []
    if reason:
        detail = {"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": reason}
        if metadata:
            detail["metadata"] = metadata
        details.append(detail)

    return {"error": {"code": 429, "message": "quota", "status": status, "details": details}}


def test_antigravity_explicit_quota_exhausted():
    body = _error_body(
        "QUOTA_EXHAUSTED",
        model="gemini-2.5-flash",
        delay="2154h21m14s",
    )
    result = extract_quota_exhaustion(body, mode="antigravity")

    assert result is not None
    assert result["model"] == "gemini-2.5-flash"
    assert result["explicit"] is True
    expected = time.time() + 2154 * 3600 + 21 * 60 + 14
    assert abs(result["reset_timestamp"] - expected) < 5
    print("PASS antigravity 显式 QUOTA_EXHAUSTED 观测")


def test_antigravity_generic_resource_exhausted_ignored():
    # 泛 RESOURCE_EXHAUSTED 可能是非配额失败（如滥用拦截），不得误冷却凭证
    body = _error_body("RESOURCE_EXHAUSTED", model="gemini-2.5-flash")
    result = extract_quota_exhaustion(body, mode="antigravity")
    assert result is None
    print("PASS antigravity 泛 RESOURCE_EXHAUSTED 不产生观测")


def test_non_quota_error_ignored():
    body = {
        "error": {
            "code": 503,
            "message": "No capacity available",
            "status": "UNAVAILABLE",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.ErrorInfo",
                    "reason": "MODEL_CAPACITY_EXHAUSTED",
                    "metadata": {"model": "gemini-2.5-flash"},
                }
            ],
        }
    }
    assert extract_quota_exhaustion(body, mode="antigravity") is None
    print("PASS 非配额错误(503 容量)不产生观测")


def test_geminicli_reset_timestamp():
    body = _error_body(
        "QUOTA_EXHAUSTED",
        model="gemini-3-flash",
        reset_ts="2033-01-15T05:00:00Z",
    )
    result = extract_quota_exhaustion(body, mode="geminicli")

    assert result is not None
    assert result["model"] == "gemini-3-flash"
    assert result["explicit"] is True
    assert result["reset_timestamp"] > time.time()
    print("PASS geminicli 绝对重置时间解析")


def test_geminicli_non_resource_exhausted_ignored():
    body = _error_body("QUOTA_EXHAUSTED", status="INVALID_ARGUMENT")
    assert extract_quota_exhaustion(body, mode="geminicli") is None
    print("PASS geminicli 非 RESOURCE_EXHAUSTED 不产生观测")


def test_malformed_input_ignored():
    assert extract_quota_exhaustion({}, mode="antigravity") is None
    assert extract_quota_exhaustion("not a dict", mode="geminicli") is None
    print("PASS 畸形输入安全返回 None")


def main():
    test_antigravity_explicit_quota_exhausted()
    test_antigravity_generic_resource_exhausted_ignored()
    test_non_quota_error_ignored()
    test_geminicli_reset_timestamp()
    test_geminicli_non_resource_exhausted_ignored()
    test_malformed_input_ignored()
    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()

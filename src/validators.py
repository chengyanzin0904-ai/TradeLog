from __future__ import annotations


def validate_trade_payload(payload: dict) -> list[str]:
    errors: list[str] = []
    if not payload.get("date"):
        errors.append("交易日期不能为空。")
    if payload.get("grade") not in {"A", "B", "C"}:
        errors.append("交易等级必须是 A/B/C。")
    if payload.get("emotion_score", 3) not in [1, 2, 3, 4, 5]:
        errors.append("情绪分数必须在 1-5 之间。")
    if payload.get("planned_risk_r", 0) <= 0:
        errors.append("计划风险 R 必须大于 0。")
    return errors

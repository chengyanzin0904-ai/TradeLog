from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date
from typing import Any


BOOL_FIELDS = {
    "is_planned",
    "fomo",
    "revenge_trade",
    "chased_after_miss",
    "traded_for_content",
    "traded_for_monthly_goal",
    "proof_mindset",
}


@dataclass
class Trade:
    trade_id: str
    date: str
    market: str = "crypto"
    symbol_private: str = ""
    symbol_public: str = "品种A"
    direction: str = "long"
    strategy_name: str = ""
    setup_type: str = ""
    timeframe_context: str = "1H"
    timeframe_entry: str = "5M"
    session: str = ""
    entry_price: float = 0.0
    stop_price: float = 0.0
    exit_price: float = 0.0
    position_size: float = 0.0
    initial_risk_amount: float = 0.0
    result_r: float = 0.0
    planned_risk_r: float = 1.0
    fees: float = 0.0
    slippage: float = 0.0
    is_planned: bool = True
    grade: str = "B"
    entry_reason: str = ""
    exit_reason: str = ""
    invalidation_condition: str = ""
    management_notes: str = ""
    emotion_before: str = ""
    emotion_during: str = ""
    emotion_after: str = ""
    emotion_score: int = 3
    fomo: bool = False
    revenge_trade: bool = False
    chased_after_miss: bool = False
    traded_for_content: bool = False
    traded_for_monthly_goal: bool = False
    proof_mindset: bool = False
    notes: str = ""
    screenshot_before_private: str = ""
    screenshot_during_private: str = ""
    screenshot_after_private: str = ""
    screenshot_public: str = ""

    @classmethod
    def empty(cls) -> "Trade":
        return cls(trade_id="", date=date.today().isoformat())

    @classmethod
    def field_names(cls) -> list[str]:
        return [field.name for field in fields(cls)]

    def to_db_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        for key in BOOL_FIELDS:
            data[key] = 1 if data.get(key) else 0
        return data

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Trade":
        data = {name: row.get(name) for name in cls.field_names()}
        for key in BOOL_FIELDS:
            data[key] = bool(data.get(key))
        return cls(**data)

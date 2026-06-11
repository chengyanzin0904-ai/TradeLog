from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import Trade
from .utils import database_path


DB_PATH = database_path()


SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    market TEXT,
    symbol_private TEXT,
    symbol_public TEXT,
    direction TEXT,
    strategy_name TEXT,
    setup_type TEXT,
    timeframe_context TEXT,
    timeframe_entry TEXT,
    session TEXT,
    entry_price REAL,
    stop_price REAL,
    exit_price REAL,
    position_size REAL,
    initial_risk_amount REAL,
    result_r REAL,
    planned_risk_r REAL,
    fees REAL,
    slippage REAL,
    is_planned INTEGER,
    grade TEXT,
    entry_reason TEXT,
    exit_reason TEXT,
    invalidation_condition TEXT,
    management_notes TEXT,
    emotion_before TEXT,
    emotion_during TEXT,
    emotion_after TEXT,
    emotion_score INTEGER,
    fomo INTEGER,
    revenge_trade INTEGER,
    chased_after_miss INTEGER,
    traded_for_content INTEGER,
    traded_for_monthly_goal INTEGER,
    proof_mindset INTEGER,
    notes TEXT,
    screenshot_before_private TEXT,
    screenshot_during_private TEXT,
    screenshot_after_private TEXT,
    screenshot_public TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL,
    period_start TEXT,
    period_end TEXT,
    file_path TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def generate_trade_id(trade_date: str, db_path: Path | str = DB_PATH) -> str:
    clean_date = trade_date.replace("-", "")
    prefix = f"T{clean_date}"
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT trade_id FROM trades WHERE trade_id LIKE ? ORDER BY trade_id DESC LIMIT 1",
            (f"{prefix}-%",),
        ).fetchone()
    next_number = 1
    if row:
        next_number = int(row["trade_id"].split("-")[-1]) + 1
    return f"{prefix}-{next_number:03d}"


def create_trade(trade: Trade, db_path: Path | str = DB_PATH) -> str:
    if not trade.trade_id:
        trade.trade_id = generate_trade_id(trade.date, db_path)
    data = trade.to_db_dict()
    columns = ", ".join(data.keys())
    placeholders = ", ".join([f":{key}" for key in data])
    with connect(db_path) as conn:
        conn.execute(f"INSERT INTO trades ({columns}) VALUES ({placeholders})", data)
    return trade.trade_id


def update_trade(trade_id: str, values: dict[str, Any], db_path: Path | str = DB_PATH) -> None:
    allowed = set(Trade.field_names()) - {"trade_id"}
    updates = {key: value for key, value in values.items() if key in allowed}
    if not updates:
        return
    updates["updated_at"] = datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join([f"{key} = :{key}" for key in updates])
    updates["trade_id"] = trade_id
    with connect(db_path) as conn:
        conn.execute(f"UPDATE trades SET {set_clause} WHERE trade_id = :trade_id", updates)


def delete_trade(trade_id: str, db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM trades WHERE trade_id = ?", (trade_id,))


def get_trade(trade_id: str, db_path: Path | str = DB_PATH) -> Trade | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM trades WHERE trade_id = ?", (trade_id,)).fetchone()
    return Trade.from_row(dict(row)) if row else None


def list_trades(db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM trades ORDER BY date DESC, trade_id DESC").fetchall()
    return [dict(row) for row in rows]


def query_trades(filters: dict[str, Any], db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if filters.get("start_date"):
        clauses.append("date >= :start_date")
        params["start_date"] = filters["start_date"]
    if filters.get("end_date"):
        clauses.append("date <= :end_date")
        params["end_date"] = filters["end_date"]
    if filters.get("symbol"):
        clauses.append("(symbol_private LIKE :symbol OR symbol_public LIKE :symbol)")
        params["symbol"] = f"%{filters['symbol']}%"
    if filters.get("strategy_name"):
        clauses.append("strategy_name LIKE :strategy_name")
        params["strategy_name"] = f"%{filters['strategy_name']}%"
    if filters.get("grade") and filters["grade"] != "全部":
        clauses.append("grade = :grade")
        params["grade"] = filters["grade"]
    if filters.get("is_planned") in (0, 1):
        clauses.append("is_planned = :is_planned")
        params["is_planned"] = filters["is_planned"]
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM trades {where} ORDER BY date DESC, trade_id DESC"
    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def seed_example_data(db_path: Path | str = DB_PATH) -> None:
    init_db(db_path)
    if list_trades(db_path):
        return
    examples = [
        Trade(
            trade_id="T20260601-001",
            date="2026-06-01",
            market="crypto",
            symbol_private="BTCUSDT",
            symbol_public="高波动品种A",
            direction="long",
            strategy_name="趋势回踩",
            setup_type="关键位回踩确认",
            result_r=1.8,
            is_planned=True,
            grade="A",
            emotion_score=4,
            entry_reason="回踩主结构后出现确认信号",
            exit_reason="达到计划目标后分批出场",
        ),
        Trade(
            trade_id="T20260603-001",
            date="2026-06-03",
            market="crypto",
            symbol_private="ETHUSDT",
            symbol_public="品种B",
            direction="short",
            strategy_name="区间失败",
            setup_type="假突破回落",
            result_r=-1.0,
            is_planned=True,
            grade="B",
            emotion_score=3,
            exit_reason="触发预设失效条件",
        ),
        Trade(
            trade_id="T20260605-001",
            date="2026-06-05",
            market="forex",
            symbol_private="XAUUSD",
            symbol_public="品种C",
            direction="long",
            strategy_name="突破追踪",
            setup_type="突破后追单",
            result_r=-0.7,
            is_planned=False,
            grade="C",
            emotion_score=2,
            fomo=True,
            chased_after_miss=True,
            notes="错过初始位置后追入，执行质量较差。",
        ),
    ]
    for trade in examples:
        create_trade(trade, db_path)

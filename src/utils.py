from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = {
    "risk": {
        "max_single_trade_r": 1,
        "max_daily_loss_r": 1.5,
        "max_weekly_loss_r": 3,
        "max_monthly_loss_r": 5,
        "pause_after_consecutive_losses": 3,
    },
    "content": {
        "add_disclaimer": True,
        "public_symbol_default": "品种A",
        "forbidden_words_check": True,
    },
    "project": {
        "name": "180天真实交易系统验证",
        "main_timeframe": "1H",
        "entry_timeframe": "5M",
        "allow_1m_signal": False,
    },
}


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        return DEFAULT_CONFIG
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    merged = DEFAULT_CONFIG.copy()
    for section, values in loaded.items():
        if isinstance(values, dict) and section in merged:
            merged[section] = {**merged[section], **values}
        else:
            merged[section] = values
    return merged


def app_data_dir() -> Path:
    return Path(os.getenv("APP_DATA_DIR", "data"))


def database_path() -> Path:
    return Path(os.getenv("TRADE_DB_PATH", app_data_dir() / "trades.db"))


def exports_dir() -> Path:
    return Path(os.getenv("TRADE_EXPORTS_DIR", app_data_dir() / "exports"))


def screenshots_dir(kind: str) -> Path:
    base = Path(os.getenv("TRADE_SCREENSHOTS_DIR", app_data_dir() / "screenshots"))
    return base / kind


def save_uploaded_file(uploaded_file, target_dir: str | Path, prefix: str) -> str:
    if uploaded_file is None:
        return ""
    folder = Path(target_dir)
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix
    path = folder / f"{prefix}{suffix}"
    path.write_bytes(uploaded_file.getbuffer())
    return str(path)

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analytics import calculate_metrics, grade_stats, to_dataframe
from .utils import exports_dir


TEMPLATES_DIR = Path("templates")


def env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_report(template_name: str, context: dict) -> str:
    template = env().get_template(template_name)
    return template.render(**context)


def report_context(trades: list[dict], title: str = "交易复盘报告") -> dict:
    df = to_dataframe(trades)
    metrics = calculate_metrics(df)
    grades = grade_stats(df).to_dict("records") if not df.empty else []
    return {
        "title": title,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "trades": trades,
        "metrics": metrics,
        "grades": grades,
    }


def export_markdown(markdown: str, report_type: str) -> Path:
    export_dir = exports_dir()
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = export_dir / filename
    path.write_text(markdown, encoding="utf-8")
    return path


def filter_period(trades: list[dict], period: str) -> list[dict]:
    if not trades:
        return []
    df = to_dataframe(trades)
    today = pd.Timestamp(date.today())
    if period == "daily":
        selected = df[df["date"].dt.date == today.date()]
    elif period == "weekly":
        selected = df[
            (df["date"].dt.isocalendar().week == today.isocalendar().week)
            & (df["date"].dt.year == today.year)
        ]
    elif period == "monthly":
        selected = df[(df["date"].dt.month == today.month) & (df["date"].dt.year == today.year)]
    else:
        selected = df
    return selected.sort_values(["date", "trade_id"], ascending=False).to_dict("records")

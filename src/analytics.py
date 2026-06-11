from __future__ import annotations

import pandas as pd


def to_dataframe(trades: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(trades)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "result_r",
                "is_planned",
                "grade",
                "strategy_name",
                "symbol_public",
                "timeframe_context",
                "emotion_score",
            ]
        )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_cols = [
        "entry_price",
        "stop_price",
        "exit_price",
        "position_size",
        "initial_risk_amount",
        "result_r",
        "planned_risk_r",
        "fees",
        "slippage",
        "emotion_score",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    bool_cols = [
        "is_planned",
        "fomo",
        "revenge_trade",
        "chased_after_miss",
        "traded_for_content",
        "traded_for_monthly_goal",
        "proof_mindset",
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    return df.sort_values(["date", "trade_id"], ascending=True)


def max_streak(values: list[float], positive: bool) -> int:
    best = 0
    current = 0
    for value in values:
        ok = value > 0 if positive else value < 0
        current = current + 1 if ok else 0
        best = max(best, current)
    return best


def current_losing_streak(values: list[float]) -> int:
    streak = 0
    for value in reversed(values):
        if value < 0:
            streak += 1
        else:
            break
    return streak


def equity_curve(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "result_r", "cumulative_r", "drawdown_r"])
    curve = df[["date", "result_r"]].copy()
    curve["cumulative_r"] = curve["result_r"].cumsum()
    peak = curve["cumulative_r"].cummax()
    curve["drawdown_r"] = curve["cumulative_r"] - peak
    return curve


def max_drawdown(df: pd.DataFrame) -> float:
    curve = equity_curve(df)
    if curve.empty:
        return 0.0
    return float(curve["drawdown_r"].min())


def current_drawdown(df: pd.DataFrame) -> float:
    curve = equity_curve(df)
    if curve.empty:
        return 0.0
    return float(curve["drawdown_r"].iloc[-1])


def grade_stats(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["grade", "count", "sum_r", "avg_r"])
    grouped = (
        df.groupby("grade", dropna=False)["result_r"]
        .agg(count="count", sum_r="sum", avg_r="mean")
        .reset_index()
        .sort_values("grade")
    )
    return grouped


def period_r(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["period", "result_r"])
    grouped = df.set_index("date")["result_r"].resample(freq).sum().reset_index()
    grouped["period"] = grouped["date"].dt.strftime("%Y-%m-%d" if freq == "D" else "%Y-%m")
    if freq == "W":
        grouped["period"] = grouped["date"].dt.strftime("%G-W%V")
    return grouped[["period", "result_r"]]


def grouped_r(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, "result_r"])
    return df.groupby(column, dropna=False)["result_r"].sum().reset_index()


def calculate_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_trades": 0,
            "total_r": 0.0,
            "average_r": 0.0,
            "win_rate": 0.0,
            "avg_win_r": 0.0,
            "avg_loss_r": 0.0,
            "profit_loss_ratio": 0.0,
            "expectancy": 0.0,
            "max_win_r": 0.0,
            "max_loss_r": 0.0,
            "max_win_streak": 0,
            "max_loss_streak": 0,
            "max_drawdown_r": 0.0,
            "current_drawdown_r": 0.0,
            "planned_ratio": 0.0,
            "c_grade_ratio": 0.0,
            "unplanned_total_r": 0.0,
            "current_loss_streak": 0,
            "fomo_count": 0,
            "revenge_trade_count": 0,
            "chased_after_miss_count": 0,
            "traded_for_content_count": 0,
            "traded_for_monthly_goal_count": 0,
            "proof_mindset_count": 0,
        }

    results = df["result_r"].astype(float)
    wins = results[results > 0]
    losses = results[results < 0]
    win_rate = len(wins) / len(results) if len(results) else 0
    avg_win = wins.mean() if not wins.empty else 0.0
    avg_loss = losses.mean() if not losses.empty else 0.0
    loss_rate = len(losses) / len(results) if len(results) else 0
    expectancy = win_rate * avg_win + loss_rate * avg_loss
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss else 0.0

    return {
        "total_trades": int(len(df)),
        "total_r": float(results.sum()),
        "average_r": float(results.mean()),
        "win_rate": float(win_rate),
        "avg_win_r": float(avg_win),
        "avg_loss_r": float(avg_loss),
        "profit_loss_ratio": float(profit_loss_ratio),
        "expectancy": float(expectancy),
        "max_win_r": float(results.max()),
        "max_loss_r": float(results.min()),
        "max_win_streak": max_streak(results.tolist(), positive=True),
        "max_loss_streak": max_streak(results.tolist(), positive=False),
        "max_drawdown_r": max_drawdown(df),
        "current_drawdown_r": current_drawdown(df),
        "planned_ratio": float(df["is_planned"].mean()) if "is_planned" in df else 0.0,
        "c_grade_ratio": float((df["grade"] == "C").mean()) if "grade" in df else 0.0,
        "unplanned_total_r": float(df.loc[~df["is_planned"], "result_r"].sum()) if "is_planned" in df else 0.0,
        "current_loss_streak": current_losing_streak(results.tolist()),
        "fomo_count": int(df.get("fomo", pd.Series(dtype=bool)).sum()),
        "revenge_trade_count": int(df.get("revenge_trade", pd.Series(dtype=bool)).sum()),
        "chased_after_miss_count": int(df.get("chased_after_miss", pd.Series(dtype=bool)).sum()),
        "traded_for_content_count": int(df.get("traded_for_content", pd.Series(dtype=bool)).sum()),
        "traded_for_monthly_goal_count": int(df.get("traded_for_monthly_goal", pd.Series(dtype=bool)).sum()),
        "proof_mindset_count": int(df.get("proof_mindset", pd.Series(dtype=bool)).sum()),
    }


def risk_status(df: pd.DataFrame, risk_config: dict) -> list[str]:
    if df.empty:
        return ["暂无交易记录，风控状态正常。"]
    today = pd.Timestamp.today().normalize()
    current_week = today.isocalendar().week
    current_month = today.month
    current_year = today.year

    today_r = df.loc[df["date"].dt.normalize() == today, "result_r"].sum()
    week_r = df.loc[
        (df["date"].dt.isocalendar().week == current_week) & (df["date"].dt.year == current_year),
        "result_r",
    ].sum()
    month_r = df.loc[
        (df["date"].dt.month == current_month) & (df["date"].dt.year == current_year),
        "result_r",
    ].sum()
    metrics = calculate_metrics(df)

    messages: list[str] = []
    if today_r <= -abs(risk_config.get("max_daily_loss_r", 1.5)):
        messages.append("今日已达到最大亏损线，建议停止交易并复盘。")
    if week_r <= -abs(risk_config.get("max_weekly_loss_r", 3)):
        messages.append("本周已触及周度风险线，建议降低频率。")
    if month_r <= -abs(risk_config.get("max_monthly_loss_r", 5)):
        messages.append("本月已达到停止进攻线，只允许复盘。")
    if metrics["current_loss_streak"] >= risk_config.get("pause_after_consecutive_losses", 3):
        messages.append("已出现连续亏损，建议暂停正式交易。")
    return messages or ["当前未触发主要风控红线。"]

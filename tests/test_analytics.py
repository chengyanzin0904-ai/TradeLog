import pandas as pd

from src.analytics import calculate_metrics, grade_stats, max_drawdown, to_dataframe


def sample_df():
    trades = [
        {"trade_id": "T1", "date": "2026-06-01", "result_r": 1.0, "is_planned": 1, "grade": "A"},
        {"trade_id": "T2", "date": "2026-06-02", "result_r": -1.0, "is_planned": 1, "grade": "B"},
        {"trade_id": "T3", "date": "2026-06-03", "result_r": 2.0, "is_planned": 0, "grade": "A"},
        {"trade_id": "T4", "date": "2026-06-04", "result_r": -0.5, "is_planned": 0, "grade": "C"},
        {"trade_id": "T5", "date": "2026-06-05", "result_r": -0.5, "is_planned": 1, "grade": "C"},
    ]
    return to_dataframe(trades)


def test_total_r_and_win_rate():
    metrics = calculate_metrics(sample_df())
    assert metrics["total_r"] == 1.0
    assert metrics["win_rate"] == 0.4


def test_average_win_and_loss_r():
    metrics = calculate_metrics(sample_df())
    assert metrics["avg_win_r"] == 1.5
    assert metrics["avg_loss_r"] == -2 / 3


def test_max_drawdown():
    df = sample_df()
    assert max_drawdown(df) == -1.0


def test_max_consecutive_losses():
    metrics = calculate_metrics(sample_df())
    assert metrics["max_loss_streak"] == 2


def test_planned_ratio():
    metrics = calculate_metrics(sample_df())
    assert metrics["planned_ratio"] == 0.6


def test_grade_stats():
    stats = grade_stats(sample_df())
    by_grade = {row["grade"]: row for row in stats.to_dict("records")}
    assert by_grade["A"]["count"] == 2
    assert by_grade["A"]["sum_r"] == 3.0
    assert by_grade["C"]["count"] == 2
    assert by_grade["C"]["sum_r"] == -1.0

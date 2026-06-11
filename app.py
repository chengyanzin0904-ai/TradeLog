from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import (
    calculate_metrics,
    equity_curve,
    grade_stats,
    grouped_r,
    period_r,
    risk_status,
    to_dataframe,
)
from src.database import (
    create_trade,
    delete_trade,
    get_trade,
    init_db,
    list_trades,
    query_trades,
    seed_example_data,
    update_trade,
)
from src.models import Trade
from src.reports import export_markdown, filter_period, render_report, report_context
from src.sanitizer import public_trade_summary, sanitize_public_content, scan_text
from src.utils import load_config, save_uploaded_file, screenshots_dir
from src.validators import validate_trade_payload


st.set_page_config(page_title="真实交易成长记录流水线", page_icon="📈", layout="wide")

init_db()
config = load_config()


DISCIPLINE_RULES = [
    "交易结果只评价策略和执行，不评价个人价值。",
    "没进场的利润不属于我。",
    "月度目标不得影响单笔决策。",
    "错过后必须重新定价，不允许追单。",
    "连续亏损 3 笔后暂停正式交易。",
    "当月达到 -5R，停止进攻，只允许复盘。",
    "内容不能反向驱动交易。",
    "不为做曲线而交易。",
    "不为证明自己而交易。",
    "公开内容不喊单、不承诺收益、不诱导交易。",
]


def refresh_trades() -> list[dict]:
    return list_trades()


def metric_card(label: str, value: str) -> None:
    st.metric(label, value)


def trade_form(default: Trade | None = None, key_prefix: str = "create") -> dict:
    default = default or Trade.empty()
    c1, c2, c3 = st.columns(3)
    with c1:
        trade_date = st.date_input("交易日期", value=pd.to_datetime(default.date).date(), key=f"{key_prefix}_date")
        market = st.selectbox("市场类型", ["crypto", "forex", "stocks", "futures", "other"], index=0, key=f"{key_prefix}_market")
        symbol_private = st.text_input("私密品种名称", value=default.symbol_private, key=f"{key_prefix}_symbol_private")
        symbol_public = st.text_input("公开脱敏名称", value=default.symbol_public, key=f"{key_prefix}_symbol_public")
        direction = st.selectbox("方向", ["long", "short"], index=0 if default.direction == "long" else 1, key=f"{key_prefix}_direction")
    with c2:
        strategy_name = st.text_input("策略名称", value=default.strategy_name, key=f"{key_prefix}_strategy_name")
        setup_type = st.text_input("交易形态/场景", value=default.setup_type, key=f"{key_prefix}_setup_type")
        timeframe_context = st.text_input("主周期", value=default.timeframe_context, key=f"{key_prefix}_timeframe_context")
        timeframe_entry = st.text_input("入场周期", value=default.timeframe_entry, key=f"{key_prefix}_timeframe_entry")
        session = st.text_input("交易时段", value=default.session, key=f"{key_prefix}_session")
    with c3:
        entry_price = st.number_input("入场价", value=float(default.entry_price), step=0.01, key=f"{key_prefix}_entry_price")
        stop_price = st.number_input("止损价", value=float(default.stop_price), step=0.01, key=f"{key_prefix}_stop_price")
        exit_price = st.number_input("出场价", value=float(default.exit_price), step=0.01, key=f"{key_prefix}_exit_price")
        position_size = st.number_input("仓位数量", value=float(default.position_size), step=0.01, key=f"{key_prefix}_position_size")
        initial_risk_amount = st.number_input("初始风险金额", value=float(default.initial_risk_amount), step=0.01, key=f"{key_prefix}_initial_risk_amount")

    c4, c5, c6 = st.columns(3)
    with c4:
        result_r = st.number_input("结果 R", value=float(default.result_r), step=0.1, key=f"{key_prefix}_result_r")
        planned_risk_r = st.number_input("计划风险 R", value=float(default.planned_risk_r), step=0.1, min_value=0.1, key=f"{key_prefix}_planned_risk_r")
        fees = st.number_input("手续费", value=float(default.fees), step=0.01, key=f"{key_prefix}_fees")
        slippage = st.number_input("滑点", value=float(default.slippage), step=0.01, key=f"{key_prefix}_slippage")
    with c5:
        is_planned = st.checkbox("是否计划内", value=default.is_planned, key=f"{key_prefix}_is_planned")
        grade = st.selectbox("执行等级", ["A", "B", "C"], index=["A", "B", "C"].index(default.grade), key=f"{key_prefix}_grade")
        emotion_score = st.slider("情绪分数", 1, 5, int(default.emotion_score), key=f"{key_prefix}_emotion_score")
    with c6:
        fomo = st.checkbox("FOMO", value=default.fomo, key=f"{key_prefix}_fomo")
        revenge_trade = st.checkbox("报复交易", value=default.revenge_trade, key=f"{key_prefix}_revenge_trade")
        chased_after_miss = st.checkbox("错过后追单", value=default.chased_after_miss, key=f"{key_prefix}_chased_after_miss")
        traded_for_content = st.checkbox("为了发内容而交易", value=default.traded_for_content, key=f"{key_prefix}_traded_for_content")
        traded_for_monthly_goal = st.checkbox("为了月度目标而交易", value=default.traded_for_monthly_goal, key=f"{key_prefix}_traded_for_monthly_goal")
        proof_mindset = st.checkbox("为了证明自己而交易", value=default.proof_mindset, key=f"{key_prefix}_proof_mindset")

    entry_reason = st.text_area("入场理由", value=default.entry_reason, key=f"{key_prefix}_entry_reason")
    exit_reason = st.text_area("出场理由", value=default.exit_reason, key=f"{key_prefix}_exit_reason")
    invalidation_condition = st.text_area("失效条件", value=default.invalidation_condition, key=f"{key_prefix}_invalidation_condition")
    management_notes = st.text_area("持仓管理记录", value=default.management_notes, key=f"{key_prefix}_management_notes")
    emotion_before = st.text_input("入场前情绪", value=default.emotion_before, key=f"{key_prefix}_emotion_before")
    emotion_during = st.text_input("持仓中情绪", value=default.emotion_during, key=f"{key_prefix}_emotion_during")
    emotion_after = st.text_input("出场后情绪", value=default.emotion_after, key=f"{key_prefix}_emotion_after")
    notes = st.text_area("备注", value=default.notes, key=f"{key_prefix}_notes")

    uploads = st.columns(4)
    with uploads[0]:
        before_file = st.file_uploader("入场前私密截图", type=["png", "jpg", "jpeg"], key=f"{key_prefix}_before_file")
    with uploads[1]:
        during_file = st.file_uploader("持仓中私密截图", type=["png", "jpg", "jpeg"], key=f"{key_prefix}_during_file")
    with uploads[2]:
        after_file = st.file_uploader("出场后私密截图", type=["png", "jpg", "jpeg"], key=f"{key_prefix}_after_file")
    with uploads[3]:
        public_file = st.file_uploader("公开截图", type=["png", "jpg", "jpeg"], key=f"{key_prefix}_public_file")

    temp_prefix = f"{trade_date.strftime('%Y%m%d')}_{symbol_public or 'trade'}"
    return {
        "date": trade_date.isoformat(),
        "market": market,
        "symbol_private": symbol_private,
        "symbol_public": symbol_public or config["content"]["public_symbol_default"],
        "direction": direction,
        "strategy_name": strategy_name,
        "setup_type": setup_type,
        "timeframe_context": timeframe_context,
        "timeframe_entry": timeframe_entry,
        "session": session,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "exit_price": exit_price,
        "position_size": position_size,
        "initial_risk_amount": initial_risk_amount,
        "result_r": result_r,
        "planned_risk_r": planned_risk_r,
        "fees": fees,
        "slippage": slippage,
        "is_planned": is_planned,
        "grade": grade,
        "entry_reason": entry_reason,
        "exit_reason": exit_reason,
        "invalidation_condition": invalidation_condition,
        "management_notes": management_notes,
        "emotion_before": emotion_before,
        "emotion_during": emotion_during,
        "emotion_after": emotion_after,
        "emotion_score": emotion_score,
        "fomo": fomo,
        "revenge_trade": revenge_trade,
        "chased_after_miss": chased_after_miss,
        "traded_for_content": traded_for_content,
        "traded_for_monthly_goal": traded_for_monthly_goal,
        "proof_mindset": proof_mindset,
        "notes": notes,
        "screenshot_before_private": save_uploaded_file(before_file, screenshots_dir("private"), f"{temp_prefix}_before") or default.screenshot_before_private,
        "screenshot_during_private": save_uploaded_file(during_file, screenshots_dir("private"), f"{temp_prefix}_during") or default.screenshot_during_private,
        "screenshot_after_private": save_uploaded_file(after_file, screenshots_dir("private"), f"{temp_prefix}_after") or default.screenshot_after_private,
        "screenshot_public": save_uploaded_file(public_file, screenshots_dir("public"), f"{temp_prefix}_public") or default.screenshot_public,
    }


def dashboard() -> None:
    trades = refresh_trades()
    df = to_dataframe(trades)
    metrics = calculate_metrics(df)
    project_name = config["project"]["name"]
    st.title(project_name)
    st.caption("本地化个人交易复盘与系统验证工具。公开内容默认强调风控、执行和复盘，不构成投资建议。")

    today = pd.Timestamp(date.today())
    today_r = df.loc[df["date"].dt.date == today.date(), "result_r"].sum() if not df.empty else 0
    week_r = (
        df.loc[
            (df["date"].dt.isocalendar().week == today.isocalendar().week) & (df["date"].dt.year == today.year),
            "result_r",
        ].sum()
        if not df.empty
        else 0
    )
    month_r = (
        df.loc[(df["date"].dt.month == today.month) & (df["date"].dt.year == today.year), "result_r"].sum()
        if not df.empty
        else 0
    )

    cols = st.columns(6)
    values = [
        ("今日 R", f"{today_r:.2f}R"),
        ("本周 R", f"{week_r:.2f}R"),
        ("本月 R", f"{month_r:.2f}R"),
        ("累计 R", f"{metrics['total_r']:.2f}R"),
        ("当前回撤", f"{metrics['current_drawdown_r']:.2f}R"),
        ("最大回撤", f"{metrics['max_drawdown_r']:.2f}R"),
    ]
    for col, (label, value) in zip(cols, values):
        with col:
            metric_card(label, value)

    cols2 = st.columns(5)
    more_values = [
        ("总交易数", str(metrics["total_trades"])),
        ("计划内比例", f"{metrics['planned_ratio']:.0%}"),
        ("C 级占比", f"{metrics['c_grade_ratio']:.0%}"),
        ("连续亏损", str(metrics["current_loss_streak"])),
        ("胜率", f"{metrics['win_rate']:.0%}"),
    ]
    for col, (label, value) in zip(cols2, more_values):
        with col:
            metric_card(label, value)

    left, right = st.columns([1, 1])
    with left:
        st.subheader("风控状态")
        for message in risk_status(df, config["risk"]):
            st.info(message)
        st.subheader("纪律提醒")
        for idx, rule in enumerate(DISCIPLINE_RULES, start=1):
            st.write(f"{idx}. {rule}")
    with right:
        st.subheader("最近 5 笔交易")
        if trades:
            st.dataframe(pd.DataFrame(trades).head(5), use_container_width=True)
        else:
            st.warning("暂无交易。可以先录入一笔，或导入示例数据。")
            if st.button("导入示例交易数据"):
                seed_example_data()
                st.rerun()


def charts() -> None:
    trades = refresh_trades()
    df = to_dataframe(trades)
    st.header("统计与图表")
    if df.empty:
        st.warning("暂无数据。")
        return

    metrics = calculate_metrics(df)
    summary = pd.DataFrame(
        [
            ["总 R", metrics["total_r"]],
            ["平均 R", metrics["average_r"]],
            ["胜率", metrics["win_rate"]],
            ["盈亏比", metrics["profit_loss_ratio"]],
            ["期望值", metrics["expectancy"]],
            ["最大连续亏损", metrics["max_loss_streak"]],
        ],
        columns=["指标", "值"],
    )
    st.dataframe(summary, use_container_width=True)

    curve = equity_curve(df)
    st.plotly_chart(px.line(curve, x="date", y="cumulative_r", title="累计 R 净值曲线"), use_container_width=True)
    st.plotly_chart(px.area(curve, x="date", y="drawdown_r", title="回撤曲线"), use_container_width=True)
    st.plotly_chart(px.bar(period_r(df, "M"), x="period", y="result_r", title="月度 R"), use_container_width=True)
    st.plotly_chart(px.bar(grade_stats(df), x="grade", y="sum_r", title="A/B/C 等级收益对比"), use_container_width=True)
    st.plotly_chart(px.bar(grouped_r(df, "is_planned"), x="is_planned", y="result_r", title="计划内 vs 计划外收益"), use_container_width=True)
    st.plotly_chart(px.scatter(df, x="emotion_score", y="result_r", color="grade", title="情绪分数与交易结果"), use_container_width=True)
    chased = df.assign(chased_count=df["chased_after_miss"].astype(int)).set_index("date")["chased_count"].resample("W").sum().reset_index()
    st.plotly_chart(px.line(chased, x="date", y="chased_count", title="错过后追单次数趋势"), use_container_width=True)


def create_trade_page() -> None:
    st.header("录入交易")
    payload = trade_form()
    if st.button("保存交易", type="primary"):
        errors = validate_trade_payload(payload)
        if errors:
            for error in errors:
                st.error(error)
            return
        trade = Trade(trade_id="", **payload)
        trade_id = create_trade(trade)
        st.success(f"已保存交易：{trade_id}")


def list_and_edit_page() -> None:
    st.header("交易列表与编辑")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        start_date = st.text_input("开始日期", placeholder="YYYY-MM-DD")
    with c2:
        end_date = st.text_input("结束日期", placeholder="YYYY-MM-DD")
    with c3:
        symbol = st.text_input("品种")
    with c4:
        strategy_name = st.text_input("策略")
    with c5:
        grade = st.selectbox("等级", ["全部", "A", "B", "C"])
    planned_choice = st.selectbox("是否计划内", ["全部", "是", "否"])
    is_planned = {"全部": None, "是": 1, "否": 0}[planned_choice]
    trades = query_trades(
        {
            "start_date": start_date or None,
            "end_date": end_date or None,
            "symbol": symbol,
            "strategy_name": strategy_name,
            "grade": grade,
            "is_planned": is_planned,
        }
    )
    st.dataframe(pd.DataFrame(trades), use_container_width=True)
    if not trades:
        return

    selected_id = st.selectbox("选择一笔交易查看/编辑", [t["trade_id"] for t in trades])
    selected = get_trade(selected_id)
    if selected:
        with st.expander("交易详情与编辑", expanded=False):
            payload = trade_form(selected, key_prefix="edit")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("更新交易"):
                    errors = validate_trade_payload(payload)
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        update_trade(selected_id, payload)
                        st.success("已更新。")
                        st.rerun()
            with col_b:
                confirm = st.checkbox("我确认要删除这笔交易")
                if st.button("删除交易", disabled=not confirm):
                    delete_trade(selected_id)
                    st.success("已删除。")
                    st.rerun()


def reports_page() -> None:
    st.header("报告生成")
    trades = refresh_trades()
    report_type = st.selectbox("报告类型", ["daily", "weekly", "monthly"])
    template_map = {
        "daily": "daily_review.md.j2",
        "weekly": "weekly_report.md.j2",
        "monthly": "monthly_report.md.j2",
    }
    title_map = {"daily": "每日复盘", "weekly": "周报", "monthly": "月报"}
    period_trades = filter_period(trades, report_type)
    markdown = render_report(template_map[report_type], report_context(period_trades, title_map[report_type]))
    st.text_area("Markdown 预览", markdown, height=520)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("下载 Markdown", markdown, file_name=f"{report_type}_report.md", mime="text/markdown")
    with c2:
        if st.button("保存到 data/exports"):
            path = export_markdown(markdown, report_type)
            st.success(f"已导出：{path}")


def public_content_page() -> None:
    st.header("公开内容生成与安全检查")
    trades = refresh_trades()
    if not trades:
        st.warning("暂无交易记录。")
        return
    selected_id = st.selectbox("选择交易", [t["trade_id"] for t in trades])
    selected = next(t for t in trades if t["trade_id"] == selected_id)
    markdown, findings = public_trade_summary(selected, config["content"]["add_disclaimer"])
    st.text_area("脱敏公开内容", markdown, height=460)
    if findings:
        st.warning("发现敏感词，已给出替换后的版本。")
        st.dataframe(pd.DataFrame([f.__dict__ for f in findings]), use_container_width=True)
    else:
        st.success("未发现敏感词。")
    st.download_button("下载公开内容 Markdown", markdown, file_name=f"public_post_{selected_id}.md", mime="text/markdown")

    st.subheader("手动安全检查")
    raw = st.text_area("粘贴公开内容草稿")
    if st.button("检查并替换"):
        clean, manual_findings = sanitize_public_content(raw, config["content"]["add_disclaimer"])
        if manual_findings:
            st.warning("发现以下敏感词：")
            st.dataframe(pd.DataFrame([f.__dict__ for f in manual_findings]), use_container_width=True)
        else:
            st.success("未发现敏感词。")
        st.text_area("替换后内容", clean, height=300)


def main() -> None:
    st.sidebar.title("真实交易成长记录")
    page = st.sidebar.radio(
        "功能",
        ["首页 Dashboard", "录入交易", "交易列表", "统计图表", "报告导出", "公开内容"],
    )
    if st.sidebar.button("初始化数据库"):
        init_db()
        st.sidebar.success("数据库已初始化。")

    if page == "首页 Dashboard":
        dashboard()
    elif page == "录入交易":
        create_trade_page()
    elif page == "交易列表":
        list_and_edit_page()
    elif page == "统计图表":
        charts()
    elif page == "报告导出":
        reports_page()
    elif page == "公开内容":
        public_content_page()


if __name__ == "__main__":
    main()

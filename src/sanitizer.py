from __future__ import annotations

from dataclasses import dataclass


DISCLAIMER = "声明：本文仅为个人交易复盘和学习记录，不构成任何投资建议。交易存在风险，历史结果不代表未来表现。请独立判断并控制风险。"


FORBIDDEN_WORDS = {
    "导流类": ["开户", "开户链接", "注册链接", "返佣", "返手续费", "交易所", "平台邀请码", "邀请码"],
    "喊单类": ["现价进", "跟上", "冲", "满仓", "梭哈", "买入", "卖出", "做多", "做空", "最后机会"],
    "收益诱导类": ["稳定盈利", "保证赚钱", "翻身", "暴富", "月入", "日赚", "带你赚钱", "跟我赚", "零风险"],
    "高风险交易类": ["高杠杆", "百倍", "爆赚", "一夜翻倍", "合约暴利"],
}


REPLACEMENTS = {
    "做多": "交易方向",
    "做空": "交易方向",
    "买入": "入场",
    "卖出": "出场",
    "翻身": "改善交易表现",
    "稳定盈利": "长期验证",
    "保证赚钱": "持续复盘",
    "暴富": "改善执行质量",
    "跟上": "仅供复盘参考",
    "现价进": "当时的入场计划",
    "满仓": "风险暴露过高",
    "梭哈": "风险暴露过高",
    "交易所": "平台",
    "高杠杆": "高风险",
    "百倍": "高风险",
    "爆赚": "结果较好",
    "一夜翻倍": "短期波动较大",
    "合约暴利": "高风险交易结果",
}


@dataclass
class Finding:
    category: str
    word: str
    replacement: str | None = None


def scan_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for category, words in FORBIDDEN_WORDS.items():
        for word in words:
            if word in text:
                findings.append(Finding(category, word, REPLACEMENTS.get(word)))
    return findings


def apply_replacements(text: str) -> str:
    clean = text
    for source, target in REPLACEMENTS.items():
        clean = clean.replace(source, target)
    return clean


def ensure_disclaimer(text: str) -> str:
    if DISCLAIMER in text:
        return text
    return f"{text.rstrip()}\n\n{DISCLAIMER}"


def sanitize_public_content(text: str, add_disclaimer: bool = True) -> tuple[str, list[Finding]]:
    findings = scan_text(text)
    clean = apply_replacements(text)
    if add_disclaimer:
        clean = ensure_disclaimer(clean)
    return clean, findings


def public_trade_summary(trade: dict, add_disclaimer: bool = True) -> tuple[str, list[Finding]]:
    direction = "方向判断"
    result = "正 R" if float(trade.get("result_r") or 0) > 0 else "负 R"
    content = f"""# 单笔交易复盘：{trade.get("symbol_public") or "品种A"}

这是一笔围绕「{trade.get("strategy_name") or "未命名策略"}」展开的个人复盘记录，重点关注计划、执行和风险控制。

## 交易背景
- 公开品种：{trade.get("symbol_public") or "品种A"}
- 交易方向：{direction}
- 主周期：{trade.get("timeframe_context") or "-"}
- 入场周期：{trade.get("timeframe_entry") or "-"}
- 交易形态：{trade.get("setup_type") or "-"}

## 执行复盘
- 是否计划内：{"是" if trade.get("is_planned") else "否"}
- 执行等级：{trade.get("grade") or "-"}
- 结果：{result}，具体数值仅用于个人系统验证。
- 入场依据：{trade.get("entry_reason") or "未记录"}
- 出场依据：{trade.get("exit_reason") or "未记录"}

## 心理与纪律
- 入场前：{trade.get("emotion_before") or "未记录"}
- 持仓中：{trade.get("emotion_during") or "未记录"}
- 出场后：{trade.get("emotion_after") or "未记录"}
- 纪律问题：{"存在 FOMO 或追单倾向，需要复盘。" if trade.get("fomo") or trade.get("chased_after_miss") else "未记录明显纪律问题。"}

## 下一步改进
继续把重点放在规则执行、失效条件和复盘质量上，避免让内容发布反向影响交易决策。
"""
    return sanitize_public_content(content, add_disclaimer)

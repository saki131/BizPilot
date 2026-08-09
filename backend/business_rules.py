# -*- coding: utf-8 -*-
"""2026/8/21 納品分からの業務ルール変更を集約するモジュール。

変更内容（請求対象期間の開始日が 2026/8/21 以降＝2026/9/20 締め請求書以降に適用）:
  1. 「美肌冠」「アクアカラー①②③」をノルマ対象商品として扱う（販売員・委託先の両方）
  2. 販売員の 20% 割引の基準額を 42,000 円以上 → 50,000 円以上 に変更

判定は「請求対象期間の開始日（前月21日）」を基準に行う。
請求対象期間は「前月21日〜当月20日（締め日）」のため、
2026/9/20 締め（対象期間 2026/8/21〜2026/9/20）以降が新ルールとなる。

商品IDは環境（STG/本番）で異なり得るため、対象商品は商品名で判定する。
"""
from datetime import date
from typing import Optional

# 新ルール適用の基準日（請求対象期間の開始日がこの日以降なら新ルール）
RULE_CHANGE_START_DATE = date(2026, 8, 21)

# 20% 割引（販売員）の新しい基準額
SALES_DISCOUNT_20_RATE = 0.20
SALES_DISCOUNT_20_THRESHOLD_NEW = 50000

# 新ルールで追加ノルマ対象となる商品（商品名で判定・環境非依存）
_NEW_QUOTA_TARGET_NAMES_EXACT = frozenset({"美肌冠"})
_NEW_QUOTA_TARGET_NAME_PREFIXES = ("アクアカラー",)


def billing_period_start(invoice_date: date) -> date:
    """締め日(invoice_date=20日)から請求対象期間の開始日(前月21日)を返す。"""
    if invoice_date.month == 1:
        return date(invoice_date.year - 1, 12, 21)
    return date(invoice_date.year, invoice_date.month - 1, 21)


def is_new_rule_period(period_start: Optional[date]) -> bool:
    """請求対象期間の開始日が新ルール適用日以降かを判定する。"""
    return period_start is not None and period_start >= RULE_CHANGE_START_DATE


def _is_new_quota_target_product(product_name: Optional[str]) -> bool:
    """商品名が新ルールで追加ノルマ対象となる商品かを判定する。"""
    if not product_name:
        return False
    if product_name in _NEW_QUOTA_TARGET_NAMES_EXACT:
        return True
    return any(product_name.startswith(prefix) for prefix in _NEW_QUOTA_TARGET_NAME_PREFIXES)


def is_quota_target(
    product_name: Optional[str],
    quota_target_flag: bool,
    period_start: Optional[date],
) -> bool:
    """商品がノルマ対象かを判定する。

    既存のノルマ対象フラグが立っていれば常にノルマ対象。
    加えて、新ルール期間（period_start が 2026/8/21 以降）では
    美肌冠・アクアカラー①②③ もノルマ対象として扱う。
    """
    if quota_target_flag:
        return True
    if is_new_rule_period(period_start) and _is_new_quota_target_product(product_name):
        return True
    return False


def resolve_sales_discount_threshold(rate: float, threshold_amount: int, period_start: Optional[date]) -> int:
    """販売員割引率の適用基準額を返す（新ルール期間では 20% の基準額を 50,000 に読み替える）。"""
    if is_new_rule_period(period_start) and abs(float(rate) - SALES_DISCOUNT_20_RATE) < 1e-9:
        return SALES_DISCOUNT_20_THRESHOLD_NEW
    return threshold_amount

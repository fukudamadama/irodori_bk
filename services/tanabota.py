# services/tanabota.py
from __future__ import annotations
import random
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from models import (
    TanabotaTransaction,
    TanabotaActionLog,
    Rule,
    Recipe,
    RecipeRule,
    Trigger,
    Action,
)

# ------------------------------------------------------------
# 金額算出（日本円・整数）
# ------------------------------------------------------------
def compute_amount(action_params: Dict[str, Any], amount_paid: int) -> int:
    """
    既存 seed / マスタに合わせた柔軟な解釈。
    サポート:
      - percentage/percent（割合）
      - amount（固定額）
      - roundup: {"to": 100}  → 100円単位に切り上げ差額
      - penalty_over_base: {"base_amount": 700} → max(0, amount - base)
      - random range: {"min_amount": 1, "max_amount": 1000}
      - percentage + bonus: {"percentage": 5, "level_bonus": 500}
      - growth_multiplier: {"growth_multiplier": 1.5} → 150% として扱う
    """
    p = action_params or {}
    a = int(amount_paid)

    t = p.get("type")

    # 型が無い場合はキーから推測
    if not t:
        if "percentage" in p or "percent" in p or "growth_multiplier" in p:
            t = "save_percentage"
        elif "base_amount" in p:
            t = "penalty_over_base"
        elif "min_amount" in p and "max_amount" in p:
            t = "random_range"
        elif "amount" in p:
            t = "fixed"
        elif "to" in p:
            t = "roundup"
        else:
            return 0

    if t == "save_percentage":
        # growth_multiplier(1.5) → 150% も受け入れる
        if "growth_multiplier" in p and "percentage" not in p and "percent" not in p:
            try:
                pct = int(round(float(p["growth_multiplier"]) * 100))
            except (TypeError, ValueError):
                pct = 0
        else:
            try:
                pct = int(p.get("percent", p.get("percentage", 0)) or 0)
            except (TypeError, ValueError):
                pct = 0
        amt = (a * pct) // 100 if pct > 0 else 0

        # 固定ボーナス加算（例: 109 の level_bonus）
        try:
            bonus = int(p.get("level_bonus", 0) or 0)
        except (TypeError, ValueError):
            bonus = 0
        return max(0, amt + bonus)

    if t == "fixed":
        try:
            amt = int(p.get("amount", 0) or 0)
        except (TypeError, ValueError):
            return 0
        return max(0, amt)

    if t == "roundup":
        try:
            step = int(p.get("to", 100) or 100)
        except (TypeError, ValueError):
            return 0
        if step <= 0:
            return 0
        rem = a % step
        return (step - rem) if rem else 0

    if t == "penalty_over_base":
        try:
            base = int(p.get("base_amount", 0) or 0)
        except (TypeError, ValueError):
            base = 0
        return max(0, a - base)

    if t == "random_range":
        try:
            lo = int(p.get("min_amount", 0) or 0)
            hi = int(p.get("max_amount", 0) or 0)
        except (TypeError, ValueError):
            return 0
        if hi < lo:
            lo, hi = hi, lo
        return random.randint(lo, hi) if hi > 0 else 0

    return 0

# ------------------------------------------------------------
# アクションタイプ推測（ログ用）
# ------------------------------------------------------------
def infer_action_type(p: Dict[str, Any]) -> str:
    if not p:
        return "unknown"
    if p.get("type"):
        return str(p["type"])
    if "percentage" in p or "percent" in p or "growth_multiplier" in p:
        return "save_percentage"
    if "amount" in p:
        return "fixed"
    if "to" in p:
        return "roundup"
    if "base_amount" in p:
        return "penalty_over_base"
    if "min_amount" in p and "max_amount" in p:
        return "random_range"
    if "level_bonus" in p:
        return "percentage_plus_bonus"
    return "unknown"

# ------------------------------------------------------------
# トリガ評価
# ------------------------------------------------------------
def trigger_match(
    trigger_name: str | None,
    trigger_params: Dict[str, Any] | None,
    amount_paid: int,
    *,
    category: str | None = None
) -> bool:
    name = (trigger_name or "").strip()
    tp = trigger_params or {}
    a = int(amount_paid)

    # 3) 支出発生
    if name == "支出発生":
        min_amt = tp.get("min_amount")
        if min_amt is not None:
            try:
                if a < int(min_amt):
                    return False
            except (TypeError, ValueError):
                return False
        return True

    # 4) 特定カテゴリでの支出
    if name == "特定カテゴリでの支出":
        cats = set(tp.get("categories") or [])
        if not cats:
            return True  # 定義ミスの保険（categories未設定なら素通し）
        if not category:
            return False
        return category in cats

    # 6) 条件付き支出
    if name == "条件付き支出":
        try:
            thr = int(tp.get("amount"))
        except (TypeError, ValueError):
            return False
        op = (tp.get("operator") or ">").strip()

        # カテゴリ条件が指定されていればチェック（無ければ金額条件だけで判定）
        cat_cond = tp.get("category")
        if cat_cond:
            if not category:
                return False
            if category != cat_cond:
                return False

        if   op == ">":  return a >  thr
        elif op == ">=": return a >= thr
        elif op == "<":  return a <  thr
        elif op == "<=": return a <= thr
        else:            return True  # 未知演算子は通す（デモ向け）

    # 9) ガチャタイム（支出発生時ランダム）
    if name == "ガチャタイム（支出発生時ランダム）":
        try:
            prob = int(tp.get("trigger_probability", 30))
        except (TypeError, ValueError):
            prob = 30
        prob = max(0, min(100, prob))
        return random.randint(1, 100) <= prob

    # 12) 推し活同額ミラーリング
    if name == "推し活同額ミラーリング":
        cats = set(tp.get("mirror_categories") or [])
        if not cats:
            return True  # 定義ミスの保険
        if not category:
            return False
        return category in cats

    # その他（毎週/月末/ゼロ日/レベルアップ/時刻/マイルストーン/リマインダー）はPOS即時では扱わない
    return False

# ------------------------------------------------------------
# メイン実行
# ------------------------------------------------------------
def execute_pos_payment(
    db: Session,
    *,
    user_id: int,
    amount_paid: int,
    category: str | None = None,  # ← 追加
) -> Tuple[TanabotaTransaction, List[TanabotaActionLog]]:
    """
    1) ユーザーのレシピに紐づくルール取得
    2) トリガ一致 → たなぼた額算出（整数円）
    3) ヘッダ＋ログ保存（コミットは呼び出し側）
    """
    amount_paid = int(amount_paid)

    # 1) ヘッダ先行（id採番）
    tx = TanabotaTransaction(
        user_id=user_id,
        amount_paid=amount_paid,
        tanabota_total=0,
    )
    db.add(tx)
    db.flush()  # tx.id

    # 2) ルール取得（重複排除に注意）
    q = (
        select(Rule, Trigger, Action)
        .join(RecipeRule, RecipeRule.rule_id == Rule.id)
        .join(Recipe, Recipe.id == RecipeRule.recipe_id)
        .join(Trigger, Trigger.id == Rule.trigger_id)
        .join(Action, Action.id == Rule.action_id)
        .where(and_(Recipe.user_id == user_id))
    )
    rows = db.execute(q).all()

    total = 0
    logs: List[TanabotaActionLog] = []
    seen_rule_ids: set[int] = set()

    for rule, trigger, action in rows:
        if rule.id in seen_rule_ids:
            continue
        seen_rule_ids.add(rule.id)

        if not trigger_match(trigger.name, rule.trigger_params or {}, amount_paid, category=category):
            continue

        amt = compute_amount(rule.action_params or {}, amount_paid)
        if amt <= 0:
            continue

        log = TanabotaActionLog(
            transaction_id=tx.id,
            rule_id=rule.id,
            action_id=action.id,
            action_type=infer_action_type(rule.action_params or {}),
            action_params_json=rule.action_params or {},
            tanabota_amount=amt,
            result_json=None,
        )
        db.add(log)
        logs.append(log)
        total += amt

    # 3) 合計反映
    tx.tanabota_total = total
    db.flush()

    return tx, logs

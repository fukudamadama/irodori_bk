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
    p = action_params or {}
    t = p.get("type")

    # 型が無い場合はキーから推測
    if not t:
        if "percentage" in p or "percent" in p:
            t = "save_percentage"
        elif "amount" in p:
            t = "fixed"
        elif "to" in p:
            t = "roundup"
        else:
            return 0

    if t == "save_percentage":
        try:
            pct = int(p.get("percent", p.get("percentage", 0)) or 0)
        except (TypeError, ValueError):
            return 0
        return (int(amount_paid) * pct) // 100 if pct > 0 else 0

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
        rem = int(amount_paid) % step
        return (step - rem) if rem else 0

    return 0

# ------------------------------------------------------------
# アクションタイプ推測（ログ用）
# ------------------------------------------------------------
def infer_action_type(p: Dict[str, Any]) -> str:
    if not p:
        return "unknown"
    if p.get("type"):
        return str(p["type"])
    if "percentage" in p or "percent" in p:
        return "save_percentage"
    if "amount" in p:
        return "fixed"
    if "to" in p:
        return "roundup"
    if "base_amount" in p:
        return "penalty_over_base"
    return "unknown"

# ------------------------------------------------------------
# トリガ評価
# ------------------------------------------------------------
def trigger_match(trigger_name, trigger_params, amount_paid: int, *, category: str | None = None) -> bool:
    name = (trigger_name or "").strip()
    tp = trigger_params or {}
    a = int(amount_paid)

    # 3) 支出発生（別名：支出/全ての支出）
    if name in {"支出発生"}:
        min_amt = tp.get("min_amount")
        if min_amt is not None:
            try:
                if a < int(min_amt):
                    return False
            except (TypeError, ValueError):
                return False
        return True

    # 4) 特定カテゴリでの支出  required_params: {"categories": ["string"]}
    if name == "特定カテゴリでの支出":
        cats = set(tp.get("categories") or [])
        if not category:
            return False
        return category in cats

    # 6) 条件付き支出  required_params: {"amount": number, "category": string, "operator": ">"}
    if name == "条件付き支出":
        try:
            thr = int(tp.get("amount"))
        except (TypeError, ValueError):
            return False
        op = (tp.get("operator") or ">").strip()
        if tp.get("category") and category and category != tp["category"]:
            return False
        if   op == ">":  return a >  thr
        elif op == ">=": return a >= thr
        elif op == "<":  return a <  thr
        elif op == "<=": return a <= thr
        else:            return True  # 未知演算子は通す（デモ向け）

    # 9) ガチャタイム（支出発生時ランダム） required_params: {"trigger_probability": number}
    if name == "ガチャタイム（支出発生時ランダム）":
        try:
            prob = int(tp.get("trigger_probability", 30))
        except (TypeError, ValueError):
            prob = 30
        prob = max(0, min(100, prob))
        return random.randint(1, 100) <= prob

    # 12) 推し活同額ミラーリング required_params: {"mirror_categories": ["string"]}
    if name == "推し活同額ミラーリング":
        cats = set(tp.get("mirror_categories") or [])
        if not category:
            return False
        return category in cats

    # その他（毎週/月末/ゼロ日/レベルアップ/時刻/マイルストーン/リマインダー）は POS 即時では扱わない
    return False

# ------------------------------------------------------------
# メイン実行
# ------------------------------------------------------------
def execute_pos_payment(
    db: Session,
    *,
    user_id: int,
    amount_paid: int,
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

        if not trigger_match(trigger.name, rule.trigger_params or {}, amount_paid):
            continue

        amt = compute_amount(rule.action_params or {}, amount_paid)
        if amt <= 0:
            continue

        log = TanabotaActionLog(
            transaction_id=tx.id,
            rule_id=rule.id,
            action_id=action.id,
            action_type=infer_action_type(rule.action_params or {}),  # ← 推測で格納
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

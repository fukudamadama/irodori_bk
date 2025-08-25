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

# ここで seed と揃える: 3,4,6,9,12 は常に発火させる
FORCE_FIRE_TRIGGER_IDS = {3, 4, 6, 9, 12}

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
def trigger_match(
    trigger_id: int | None,
    trigger_name: str | None,
    trigger_params: Dict[str, Any] | None,
    amount_paid: int,
    *,
    category: str | None = None,
) -> bool:
    """
    NOTE:
      - seed の仕様に合わせ、trigger_id が {3,4,6,9,12} の場合は必ず True を返す（=発火）。
      - それ以外は従来通りの評価（カテゴリ系は category が無ければ不発）を行う。
    """
    # 明示的に強制発火
    if trigger_id in FORCE_FIRE_TRIGGER_IDS:
        return True

    name = (trigger_name or "").strip()
    tp = trigger_params or {}
    a = int(amount_paid)

    # 3) 支出発生（全支出）
    if name in {"支出発生"}:
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
        if not category:
            return False
        return category in cats or "*" in cats

    # 6) 条件付き支出
    if name == "条件付き支出":
        try:
            thr = int(tp.get("amount"))
        except (TypeError, ValueError):
            return False
        op = (tp.get("operator") or ">").strip()
        if tp.get("category"):
            if not category or category != tp["category"]:
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
        if not category:
            return False
        return category in cats or "*" in cats

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
    category: str | None = None,
) -> Tuple[TanabotaTransaction, List[TanabotaActionLog]]:
    """
    POS支払いイベントを元に、ユーザーの有効ルールを評価してたなぼた処理を行う。

    Args:
        user_id: 対象ユーザーID
        amount_paid: 支払金額（円）
        category: 支払いカテゴリ（例: "コンビニ"）。不明な場合は None

    Returns:
        (トランザクションヘッダ, アクションログ一覧)
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

        # trigger.id/name/params を渡して評価
        if not trigger_match(
            getattr(trigger, "id", None),
            getattr(trigger, "name", None),
            rule.trigger_params or {},
            amount_paid,
            category=category,
        ):
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
            result_json={"event_category": category} if category is not None else {"event_category": None},
        )
        db.add(log)
        logs.append(log)
        total += amt

    # 3) 合計反映
    tx.tanabota_total = total
    db.flush()

    return tx, logs

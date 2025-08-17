from typing import Dict, Any, List, Iterable, Optional
from database import SessionLocal
from services.preference_service import PreferenceService
from services.recipe_service import RecipeService
from services.service_factory import ServiceFactory
import logging

log = logging.getLogger(__name__)

def _val(obj: Any, *keys: str, default=None):
    """dict でも ORM/Pydantic でも同じ書き方で値を取得する."""
    for k in keys:
        try:
            if isinstance(obj, dict):
                v = obj.get(k, None)
            else:
                v = getattr(obj, k, None)
        except Exception:
            v = None
        if v not in (None, "", []):
            return v
    return default

def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, Iterable) and not isinstance(x, (str, bytes, dict)):
        return list(x)
    return [x]

async def fetch_user_context(user_id: int) -> Dict[str, Any]:
    """
    同一サービス内のサービス層を直接呼び出して、
    ユーザー属性・傾向、利用中レシピ、財務レポートを集約する（HTTP自己呼び出しはしない）。
    LLMに渡す軽量サマリを返す。
    """
    try:
        with SessionLocal() as db:
            # --- DB呼び出し ---
            prefs_raw = PreferenceService.get_user_preferences(user_id, db) or []
            recipes_raw = RecipeService.get_recipes(user_id, db) or []

            # --- 属性・傾向の軽量サマリ（セッション内で完結） ---
            pref_summary: List[str] = []
            risk = invest_exp = monthly_budget = goal = horizon = None

            for p in _as_list(prefs_raw):
                q = _val(p, "question_text", "question", "key", "prompt", "title", default="Q")
                a = _val(p, "answer_text", "answer", "value", "selected_answers", default="")
                # 選択肢配列を文字列に
                if isinstance(a, (list, tuple)):
                    a = " / ".join(map(str, a))
                pref_summary.append(f"{q}: {a}")

                key = (q or "").lower()
                if ("リスク" in q) or ("risk" in key):
                    risk = a
                if any(k in key for k in ["経験", "exp", "投資歴"]):
                    invest_exp = a
                if any(k in key for k in ["予算", "budget", "毎月"]):
                    monthly_budget = a
                if ("目的" in q) or ("goal" in key):
                    goal = a
                if any(k in key for k in ["期間", "horizon", "いつまで"]):
                    horizon = a

            # --- レシピ・ルールの軽量サマリ（セッション内で完結） ---
            recipe_summary: List[str] = []
            for r in _as_list(recipes_raw):
                title = _val(r, "template_name", "name", default="レシピ")
                rules_any = _val(r, "rules", "rule_templates", default=[])
                rules = _as_list(rules_any)

                rule_lines: List[str] = []
                for rule in rules:
                    trig = _val(rule, "trigger", "trigger_template", default={})
                    act  = _val(rule, "action",  "action_template",  default={})
                    trig_name = _val(trig, "name", "type", default="trigger")
                    act_name  = _val(act,  "name", "type", default="action")
                    rule_lines.append(f"〔{trig_name}→{act_name}〕")

                recipe_summary.append(f"{title}: " + ("、".join(rule_lines) if rule_lines else "ルールなし"))

            # --- 財務データはここで作成（必要なら DB を使う想定） ---
            financial_service = ServiceFactory.create_financial_service()
            financial_data = financial_service.generate_financial_report_data(user_id, db) or {}

        # ↑この時点で DB セッションは閉じている
        # ↓ここからは DB 非依存の処理だけ
        openai_service = ServiceFactory.create_openai_service()
        insights = openai_service.generate_financial_insights(
            financial_data.get("user_preferences", []),
            financial_data.get("transactions", []),
        )

        return {
            "preferences": pref_summary[:20],
            "recipes": recipe_summary[:20],
            "risk": risk, "invest_exp": invest_exp, "monthly_budget": monthly_budget,
            "goal": goal, "horizon": horizon,
            "financial_insights": insights,
        }

    except Exception as e:
        log.exception("fetch_user_context failed for user_id=%s: %s", user_id, e)
        # 失敗時も API レイヤで扱いやすい形を返す
        return {
            "preferences": [],
            "recipes": [],
            "risk": None, "invest_exp": None, "monthly_budget": None,
            "goal": None, "horizon": None,
            "financial_insights": [],
            "error": f"{type(e).__name__}: {e}"
        }
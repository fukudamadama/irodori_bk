from typing import Dict, Any, List
from database import SessionLocal
from services.preference_service import PreferenceService
from services.recipe_service import RecipeService
from services.service_factory import ServiceFactory

async def fetch_user_context(user_id: int) -> Dict[str, Any]:
    """
    同一サービス内のサービス層を直接呼び出して、
    ユーザー属性・傾向、利用中レシピ、財務レポートを集約する（HTTP自己呼び出しはしない）。
    LLMに渡す軽量サマリを返す。
    """
    with SessionLocal() as db:
        prefs = PreferenceService.get_user_preferences(user_id, db) or []
        recipes = RecipeService.get_recipes(user_id, db) or []

        financial_service = ServiceFactory.create_financial_service()
        openai_service = ServiceFactory.create_openai_service()
        financial_data = financial_service.generate_financial_report_data(user_id, db)
        insights = openai_service.generate_financial_insights(
            financial_data.get("user_preferences", []),
            financial_data.get("transactions", []),
        )

    # 属性・傾向の軽量サマリと補助推論キー抽出
    pref_summary: List[str] = []
    risk = invest_exp = monthly_budget = goal = horizon = None
    for p in prefs if isinstance(prefs, list) else []:
        q = p.get("question_text") or p.get("question") or p.get("key") or "Q"
        a = p.get("answer_text") or p.get("answer") or p.get("value") or ""
        pref_summary.append(f"{q}: {a}")
        key = (q or "").lower()
        if any(k in key for k in ["リスク", "risk"]): risk = a
        if any(k in key for k in ["経験", "exp", "投資歴"]): invest_exp = a
        if any(k in key for k in ["予算", "budget", "毎月"]): monthly_budget = a
        if any(k in key for k in ["目的", "goal"]): goal = a
        if any(k in key for k in ["期間", "horizon", "いつまで"]): horizon = a

    # レシピ・ルールの軽量サマリ
    recipe_summary: List[str] = []
    for r in recipes if isinstance(recipes, list) else []:
        title = r.get("template_name") or r.get("name") or "レシピ"
        rules = r.get("rules") or r.get("rule_templates") or []
        rule_lines: List[str] = []
        for rule in rules:
            trig = rule.get("trigger") or rule.get("trigger_template") or {}
            act = rule.get("action") or rule.get("action_template") or {}
            trig_name = (trig.get("name") or trig.get("type") or "trigger")
            act_name  = (act.get("name") or act.get("type") or "action")
            rule_lines.append(f"〔{trig_name}→{act_name}〕")
        recipe_summary.append(f"{title}: " + ("、".join(rule_lines) if rule_lines else "ルールなし"))

    return {
        "preferences": pref_summary[:20],
        "recipes": recipe_summary[:20],
        "risk": risk, "invest_exp": invest_exp, "monthly_budget": monthly_budget,
        "goal": goal, "horizon": horizon,
        "financial_insights": insights,
    }

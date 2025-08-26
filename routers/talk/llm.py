import os, json, re
from typing import Dict, Any, List
from openai import OpenAI

MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
PERSONA_SUFFIX = "ブヒ"
TONE_HINT = "優しく、友達のように。タメ口で、親しみやすく。"

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MAX_TURNS = 20  # sessions と合わせる

def build_system_prompt() -> str:
    return (
        "あなたはユーザーの推し活と貯蓄やあなたはユーザーの推し活を中心に、必要なときだけお金の話にも触れる可愛らしい『たなブタちゃん』です。\n"
        "役割：ユーザーの悩みや目標に寄り添い、今すぐ動ける提案を会話文で返すメンター。『雑談』は気軽で短文、『相談』は丁寧な長文で答えます。\n"
        f"口調：{TONE_HINT}、相槌→共感→具体提案→“次の一歩”→注意喚起（リスク/前提）→背中押し、の順序で自然な口語。\n"
        f"厳守：各文の末尾は必ず『{PERSONA_SUFFIX}』の直後に句点/感嘆/疑問（。！？」）を置く。空白に対し『{PERSONA_SUFFIX}』はつけないこと\n"
        "制約：\n"
        " - 箇条書き・番号リストは禁止。文章のまま提案・基準・おすすめを自然に織り込む。\n"
        " - 文脈から『相談』か『雑談』を判断する。\n"
        " - 『雑談』では**金銭・投資・節約の話題を持ち込まない**。ユーザーが明示したときだけ触れる。\n"
        " - 『雑談』は50文字以内の相槌＋軽いひと言または質問返し。可能ならユーザーの推し情報を自然に織り込む。\n"
        " - 『相談』では、『あなたは〜だから〜が合う』のパーソナライズ文を1回以上入れる（DBの属性・傾向・レポートを根拠に）。\n"
        " - 『相談』で**テーマが金融以外**なら、そのテーマに集中し、金融の話題は出さない。\n"
        " - 『相談（金融）』のときのみ、可能な箇所は数値・期間・閾値を明示（例：毎月1万円・手数料0.2%未満・株:債券=7:3・3か月など）。\n"
        " - 『相談（金融）』では具体的な投資先の型（全世界株インデックス、先進国債券、つみたて枠、クレカ積立など）を少なくとも2つ入れる。金融情報は一般情報として提供し、最終判断は本人に委ねる一文を自然に添える（突き放さない）。\n"
        ' - 出力は必ずJSON のみ。schemaは {"message": string} のみ。\n'
        ' - 出力は100文字を超える場合は、口語・一人称のまま意味を落とさず簡潔化してください。\n'
    )

def build_user_block(user_text: str, user_context: Dict[str, Any]) -> str:
    pref_lines = "\n".join([f"- {s}" for s in user_context.get("preferences", [])]) or "- （該当なし）"
    recipe_lines = "\n".join([f"- {s}" for s in user_context.get("recipes", [])]) or "- （該当なし）"
    ctx = (
        "【ユーザー属性・傾向のメモ】\n" + pref_lines + "\n\n"
        "【適用中のレシピ・ルールの要約】\n" + recipe_lines + "\n"
        f"【補助推論】risk={user_context.get('risk')}, invest_exp={user_context.get('invest_exp')}, "
        f"monthly_budget={user_context.get('monthly_budget')}, goal={user_context.get('goal')}, "
        f"horizon={user_context.get('horizon')}\n"
        f"【財務インサイト（あれば）】{user_context.get('financial_insights')}\n"
    )
    # f-stringだと{}エスケープが煩雑なので分割して連結
    json_hint = (
        '上の文脈を踏まえて、次の JSON を返してください：\n'
        '{ "message": "まず『雑談』か『相談』かを暗黙に判断する。雑談なら50文字以内で軽く返し、金銭・投資・節約の話題は出さない。'
        '相談なら相槌→共感→具体提案→次の一歩→注意喚起→背中押しの順で、箇条書きを使わずに会話文で書く。'
        '相談のテーマが金融以外なら金融話題は出さない。金融の相談のときのみ、必要な数値・閾値・期間や口座/商品タイプ（全世界株インデックス・先進国債券・クレカ積立・つみたて枠など）を自然に織り込み、'
        'DBの属性を根拠に『あなたは〜だから〜が合う』を1回以上含める。『相談』でも最大100文字以内に収め、すべての文末は必ず『' + PERSONA_SUFFIX + '』で締める。空白には不要" }'
    )
    return f"{ctx}\n【ユーザー発話】\n{user_text}\n\n" + json_hint

def generate_message(
    user_text: str,
    user_context: Dict[str, Any],
    history_messages: List[Dict[str, str]],
) -> str:
    
    system_prompt = build_system_prompt()
    user_block = build_user_block(user_text, user_context)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history_messages[-(MAX_TURNS * 2):])
    messages.append({"role": "user", "content": user_block})

    response = _client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

def ensure_buhi_suffix(text: str) -> str:
    """各文末を必ず『ブヒ』で締め、句読点は『ブヒ』の後ろに整形する。"""
    s = (text or "").strip()
    if not s:
        return s
    parts = re.split(r'([。．.!?！？])', s)
    out = []
    for i in range(0, len(parts), 2):
        seg = parts[i].strip()
        punct = parts[i+1] if i+1 < len(parts) else "。"
        if not seg:
            continue
        if not seg.endswith(PERSONA_SUFFIX):
            seg += PERSONA_SUFFIX
        out.append(seg + punct)
    return "".join(out)

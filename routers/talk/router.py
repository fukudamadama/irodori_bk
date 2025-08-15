import os, json
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

from .schemas import TalkRequest, TalkResponse, TalkResult
from .sessions import get_or_create_session, append_history, reset_session as reset_session_store
from .context import fetch_user_context
from .llm import generate_message, ensure_buhi_suffix

load_dotenv()
router = APIRouter()

@router.post("/feedback", response_model=TalkResponse, summary="たなブタちゃんからアドバイスをもらう（リファクタ）")
async def talk_feedback(req: TalkRequest):
    try:
        # 1) セッション確立 & 既存履歴の取得
        session_id, history = get_or_create_session(req.session_id)

        # 2) パーソナライズ用のユーザー文脈を取得（DB直読み）
        user_ctx = await fetch_user_context(req.user_id)

        # 3) 応答生成（履歴＋文脈＋テンプレート）
        msg_json = generate_message(
            user_text=req.text,
            user_context=user_ctx,
            history_messages=list(history),
        )
        data = json.loads(msg_json)
        message_text = ensure_buhi_suffix(data.get("message", ""))

        # 4) 履歴を更新（user → assistant）
        append_history(history, "user", req.text)
        append_history(history, "assistant", message_text)

        return TalkResponse(result=TalkResult(session_id=session_id, message=message_text))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset_session", summary="会話セッションを破棄する（任意）")
async def reset_session(session_id: str):
    try:
        ok = reset_session_store(session_id)
        return {"ok": ok, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

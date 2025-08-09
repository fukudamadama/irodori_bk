import os
from fastapi import File, UploadFile, HTTPException, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
import tempfile
import httpx
import json
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

router = APIRouter(tags=["talk"])

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://localhost:50021")
MIN_SPEED = 0.1

#-----------------------------------------------------------------
#Speech To Text API
#-----------------------------------------------------------------
@router.post("/transcribe", summary="音声ファイルから文字起こしをする")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".wav"
    tmp_path = None
    try:
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Whisper API に投げる
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return {"text": transcript.text}

    finally:
        # 成否に関わらず削除
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

#-----------------------------------------------------------------
#たなブタちゃんのお返事生成
#-----------------------------------------------------------------

class TalkRequest(BaseModel):
    text: str
    
class TalkResponse(BaseModel):
    feedback: str

# たなブタちゃんにアドバイスをもらう関数
def generate_feedback(user_text: str) -> str:
    #OpenAI APIに対するプロンプト
    prompt = f"""
    ユーザーは推し活を心から楽しみたいと思っています。
    一方で、{user_text}の内容は、ユーザーのお金や推し活に関する悩みを表しています。
    コンテキストを読み取りつつ、語尾に「ブヒ」をつけて100文字以内の相槌やアドバイスを返してください。
    
    JSON形式で返してください:
    {{"feedback": "ここにコメント"}}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはお金の専門家で、ユーザーを心から応援する可愛らしいブタさんのマスコットキャラクターです。"},
            {"role": "user", "content": prompt}
        ],
        response_format={ "type": "json_object" }
    )

    return response.choices[0].message.content.strip()


@router.post("/feedback", response_model=TalkResponse, summary="たなブタちゃんから可愛いフィードバックをもらう")
async def talk_feedback(req: TalkRequest):
    try:
        feedback_json = generate_feedback(req.text)
        data = json.loads(feedback_json)
        return TalkResponse(feedback=data.get("feedback", ""))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#-----------------------------------------------------------------
#たなブタちゃんが喋っちゃう
#Text To Speech API
#-----------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str
    speaker: int = 3
    speedScale: Optional[float] = None
    pitchScale: Optional[float] = None
    intonationScale: Optional[float] = None
    volumeScale: Optional[float] = None
    prePhonemeLength: Optional[float] = None
    postPhonemeLength: Optional[float] = None

def clamp_positive(x: Optional[float], minv: float) -> Optional[float]:
    if x is None:
        return None
    try:
        v = float(x)
        return minv if v <= 0 else v
    except (TypeError, ValueError):
        return minv

@router.get("/voicevox/speakers")
async def list_speakers():
    try:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.get(f"{VOICEVOX_URL}/speakers")
            r.raise_for_status()
            return JSONResponse(r.json())
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOXに接続できません: {e}")

@router.post("/voicevox/initialize")
async def initialize_speaker(speaker: int):
    try:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(f"{VOICEVOX_URL}/initialize_speaker", params={"speaker": speaker})
            r.raise_for_status()
            return {"ok": True}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail={"where": "initialize_speaker", "body": e.response.text})
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOXに接続できません: {e}")

@router.post("/speech")
async def tts(req: TTSRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text は必須です。")

    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            q = await c.post(f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": req.speaker})
            q.raise_for_status()
            query = q.json()

            spd = clamp_positive(req.speedScale, MIN_SPEED)
            if spd is not None: query["speedScale"] = spd
            if req.pitchScale is not None: query["pitchScale"] = float(req.pitchScale)
            if req.intonationScale is not None: query["intonationScale"] = float(req.intonationScale)
            if req.volumeScale is not None: query["volumeScale"] = float(req.volumeScale)
            if req.prePhonemeLength is not None: query["prePhonemeLength"] = float(req.prePhonemeLength)
            if req.postPhonemeLength is not None: query["postPhonemeLength"] = float(req.postPhonemeLength)

            s = await c.post(f"{VOICEVOX_URL}/synthesis",
            params={"speaker": req.speaker}, json=query)
            s.raise_for_status()
            wav_bytes = s.content
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail={
            "where": "voicevox", "endpoint": str(e.request.url),
            "status": e.response.status_code, "body": e.response.text
        })
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOX呼び出しで通信エラー: {e}")

    return StreamingResponse(iter([wav_bytes]),
    media_type="audio/wav",
    headers={"Content-Disposition": 'inline; filename="voicevox_output.wav"'})
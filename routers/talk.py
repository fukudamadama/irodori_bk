import os
from fastapi import File, UploadFile, HTTPException, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
import tempfile
import httpx
import json
from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, AsyncIterator, Set, List
from openai import OpenAI
from dotenv import load_dotenv

router = APIRouter(tags=["talk"])

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://localhost:50021")

# --- Limits & defaults ---
MIN_SPEED = 0.1
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
HTTP_CONNECT_TIMEOUT = 10.0
HTTP_READ_TIMEOUT = 60.0

#-----------------------------------------------------------------
# Speech To Text API
#-----------------------------------------------------------------
@router.post("/transcribe", summary="音声ファイルから文字起こしをする")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
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
# たなブタちゃんのお返事生成
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
# Text To Speech API（VOICEVOX）
#-----------------------------------------------------------------

# --- Pydantic model with validation ---
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    # フェイルセーフ: 0–100 を許容（後段で実在チェック）
    speaker: conint(ge=0, le=100) = 3

    # 0 より大きい実数（None は可）
    speedScale: Optional[confloat(gt=0)] = None
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


async def fetch_speaker_ids() -> Set[int]:
    """VOICEVOX の /speakers から有効な speaker ID 群を取得。"""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_READ_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
        ) as c:
            r = await c.get(f"{VOICEVOX_URL}/speakers")
            r.raise_for_status()
            data = r.json()
            ids: Set[int] = set()
            for sp in data:
                # VOICEVOX のフォーマット: [{"name": "...", "styles":[{"id": 0, "name":"..."}]}]
                styles: List[dict] = sp.get("styles") or []
                for st in styles:
                    sid = st.get("id")
                    if isinstance(sid, int):
                        ids.add(sid)
            return ids
    except Exception:
        # 取得失敗時は空集合を返し、後段でフェイルセーフへ
        return set()


async def validate_speaker_or_fail(speaker: int):
    ids = await fetch_speaker_ids()
    if not ids:
        # スピーカー一覧取得に失敗した場合は、0–100 の範囲内なら通す（既存互換のフェイルセーフ）
        if 0 <= speaker <= 100:
            return
        raise HTTPException(status_code=400, detail="speaker ID の検証に失敗しました")
    if speaker not in ids:
        raise HTTPException(status_code=400, detail="無効な speaker ID です")


@router.get("/voicevox/speakers")
async def list_speakers():
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_READ_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
        ) as c:
            r = await c.get(f"{VOICEVOX_URL}/speakers")
            r.raise_for_status()
            return JSONResponse(r.json())
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOXに接続できません: {e}")


@router.post("/voicevox/initialize")
async def initialize_speaker(speaker: int):
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_READ_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
        ) as c:
            r = await c.post(f"{VOICEVOX_URL}/initialize_speaker", params={"speaker": speaker})
            r.raise_for_status()
            return {"ok": True}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail={"where": "initialize_speaker", "body": e.response.text})
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOXに接続できません: {e}")


async def _voicevox_synthesis_stream(query: dict, speaker: int) -> AsyncIterator[bytes]:
    """VOICEVOX synthesis をストリーミングしつつ、総サイズを監視する。"""
    total = 0
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(HTTP_READ_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
    ) as c:
        async with c.stream(
            "POST",
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": speaker},
            json=query,
        ) as resp:
            try:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_AUDIO_SIZE:
                        # ここで例外を投げると、クライアントには 413 を返す
                        raise HTTPException(status_code=413, detail="音声ファイルサイズが大きすぎます")
                    yield chunk
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=502, detail={
                    "where": "voicevox", "endpoint": str(e.request.url),
                    "status": e.response.status_code, "body": e.response.text
                })
            except httpx.HTTPError as e:
                raise HTTPException(status_code=502, detail=f"VOICEVOX呼び出しで通信エラー: {e}")


@router.post("/speech")
async def tts(req: TTSRequest):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text は必須です。")

    # speaker の実在チェック
    await validate_speaker_or_fail(req.speaker)

    # audio_query 生成
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(HTTP_READ_TIMEOUT, connect=HTTP_CONNECT_TIMEOUT)
        ) as c:
            q = await c.post(
                f"{VOICEVOX_URL}/audio_query",
                params={"text": text, "speaker": req.speaker},
            )
            q.raise_for_status()
            query = q.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail={
            "where": "voicevox", "endpoint": str(e.request.url),
            "status": e.response.status_code, "body": e.response.text
        })
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"VOICEVOX呼び出しで通信エラー: {e}")

    # パラメータ補正
    spd = clamp_positive(req.speedScale, MIN_SPEED)
    if spd is not None:
        query["speedScale"] = float(spd)
    if req.pitchScale is not None:
        query["pitchScale"] = float(req.pitchScale)
    if req.intonationScale is not None:
        query["intonationScale"] = float(req.intonationScale)
    if req.volumeScale is not None:
        query["volumeScale"] = float(req.volumeScale)
    if req.prePhonemeLength is not None:
        query["prePhonemeLength"] = float(req.prePhonemeLength)
    if req.postPhonemeLength is not None:
        query["postPhonemeLength"] = float(req.postPhonemeLength)

    # ストリーミングレスポンス化（総サイズを監視）
    async def streamer() -> AsyncIterator[bytes]:
        async for chunk in _voicevox_synthesis_stream(query, req.speaker):
            yield chunk

    return StreamingResponse(
        streamer(),
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="voicevox_output.wav"'}
    )
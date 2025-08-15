# routers/talk/tts.py
import os
import httpx
from typing import AsyncIterator, Set, List, Optional
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

from routers.talk.schemas import TTSRequest

router = APIRouter()

load_dotenv()

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://localhost:50021")

# --- Limits & defaults ---
MIN_SPEED = 0.1
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
HTTP_CONNECT_TIMEOUT = 10.0
HTTP_READ_TIMEOUT = 60.0


# --------------------------------
# Helpers
# --------------------------------
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


# --------------------------------
# Public APIs
# --------------------------------
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


@router.post("/speech", summary="ずんだもん音声合成を行う（リファクタ）")
async def tts(
    req: TTSRequest = Body(
        ...,
        example={
            "text": "string",
            "speaker": 3,
            "speedScale": 1.2,
            "pitchScale": 0.0,
            "intonationScale": 1.0,
            "volumeScale": 0.0,
            "prePhonemeLength": 0.0,
            "postPhonemeLength": 0.0,
        },
    )
):
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

    # パラメータ補正（0以下のspeedScaleはMIN_SPEEDに丸める）
    def clamp_float(name: str, value: Optional[float]):
        if value is not None:
            query[name] = float(value)

    spd = (req.speedScale if (req.speedScale is None or req.speedScale > 0) else MIN_SPEED)
    if spd is not None:
        query["speedScale"] = float(spd)
    clamp_float("pitchScale", req.pitchScale)
    clamp_float("intonationScale", req.intonationScale)
    clamp_float("volumeScale", req.volumeScale)
    clamp_float("prePhonemeLength", req.prePhonemeLength)
    clamp_float("postPhonemeLength", req.postPhonemeLength)

    # ストリーミングレスポンス化（総サイズを監視）
    async def streamer() -> AsyncIterator[bytes]:
        async for chunk in _voicevox_synthesis_stream(query, req.speaker):
            yield chunk

    return StreamingResponse(
        streamer(),
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="voicevox_output.wav"'}
    )

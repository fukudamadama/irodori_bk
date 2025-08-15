import os, tempfile
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv

router = APIRouter()
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/transcribe", summary="音声ファイルから文字起こしをする（リファクタ）")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return {"text": transcript.text}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass

import os
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter
from tempfile import NamedTemporaryFile
import tempfile
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

router = APIRouter(tags=["talk"])

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # ファイル拡張子を保持
    suffix = os.path.splitext(file.filename)[1] or ".wav"
    # 一時ファイルに書き出し
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Whisper API に投げる
    with open(tmp_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    os.remove(tmp_path)
    return {"text": transcript.text}
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter
from tempfile import NamedTemporaryFile
import tempfile
import json
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

router = APIRouter(tags=["talk"])

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

#-----------------------------------------------------------------
#Speech To Text API
#-----------------------------------------------------------------
@router.post("/transcribe",summary="音声ファイルから文字起こしをする")
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

#たなブタちゃんにアドバイスをもらう
class talk(BaseModel):
    tanabuta_talk: str

@router.post("/feedback", response_model=TalkResponse,summary="たなブタちゃんから可愛いフィードバックをもらう")
async def talk_feedback(req: TalkRequest):
    """
    たなブタちゃんに悩みを聞いてもらう
    """
    try:
        # たなブタちゃんのお返事関数を呼び出す
        feedback = generate_feedback(req.text)
        return TalkResponse(feedback=feedback)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#-----------------------------------------------------------------
#たなブタちゃんが喋っちゃう
#Text To Speech API
#-----------------------------------------------------------------

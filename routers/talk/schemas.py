from pydantic import BaseModel, Field, conint, confloat
from typing import Optional

# /talk/feedback
class TalkRequest(BaseModel):
    text: str
    user_id: int = Field(..., ge=1, description="onboarding から文脈を引くためのユーザーID")
    session_id: Optional[str] = Field(None, description="セッション継続用。未指定ならサーバで採番")

class TalkResult(BaseModel):
    session_id: str
    message: str

class TalkResponse(BaseModel):
    result: TalkResult  # 完全に result のみを返す

# /talk/speech（VOICEVOX）
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
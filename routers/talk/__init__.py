from fastapi import APIRouter
from .router import router as _talk_core
from .stt import router as _stt
from .tts import router as _tts

# すべて「talk」タグにまとめて公開
router = APIRouter()
router.include_router(_talk_core, tags=["talk"])
router.include_router(_stt, tags=["talk"])
router.include_router(_tts, tags=["talk"])

__all__ = ["router"]
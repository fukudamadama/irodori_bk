import uuid
from collections import deque
from typing import Dict, Deque, Tuple, Optional, List, TypedDict

MAX_TURNS = 20  # keep last N turns (user+assistantで×2)
Message = TypedDict("Message", {"role": str, "content": str})

# schema: { session_id: deque[Message, ...] }
SESSION_STORE: Dict[str, Deque[Message]] = {}

def get_or_create_session(session_id: Optional[str]) -> Tuple[str, Deque[Message]]:
    """Return (session_id, history_deque). Create when absent."""
    if not session_id:
        session_id = str(uuid.uuid4())
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = deque(maxlen=MAX_TURNS * 2)
    return session_id, SESSION_STORE[session_id]

def append_history(history: Deque[Message], role: str, content: str) -> None:
    history.append({"role": role, "content": content})

def reset_session(session_id: str) -> bool:
    return SESSION_STORE.pop(session_id, None) is not None

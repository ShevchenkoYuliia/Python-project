from datetime import datetime, timedelta
from typing import Dict
from src.models.session_model import Session

class SessionService:
    def __init__(self, expiration_minutes: int = 1):
        self.sessions: Dict[str, Session] = {}
        self.expiration_minutes = expiration_minutes

    def create_session(self, session_id: str, aes_key: str, iv: str) -> Session:
        expired_at = datetime.utcnow() + timedelta(minutes=self.expiration_minutes)
        session = Session(session_id=session_id, aes_key=aes_key, iv=iv, expired_at=expired_at)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def validate_session(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if not session:
            return False
        if datetime.utcnow() > session.expired_at:
            session.is_valid = False
            return False
        return True

    def get_all_sessions(self):
        return list(self.sessions.values())
session_service = SessionService()
def get_session_service() -> SessionService:
    return session_service
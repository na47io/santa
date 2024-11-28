from uuid import UUID, uuid4
from pydantic import BaseModel
from fastapi import Cookie, Response
from sqlalchemy.orm import Session
from typing import Optional
from .database import SessionStore
import json

class SessionData(BaseModel):
    answers: dict = {}
    budget: int | None = None
    current_step: int = 1
    questions: list = []
    recipient: str = ""
    summary: str | None = None
    suggestions: list = []

class SessionManager:
    def __init__(self, db: Session):
        self.db = db
        
    async def get_session(self, session_id: Optional[str] = None) -> tuple[UUID, SessionData]:
        """Get or create a session"""
        if session_id:
            db_session = self.db.query(SessionStore).filter(SessionStore.id == session_id).first()
            if db_session:
                return UUID(session_id), SessionData(**json.loads(db_session.data))
        
        # Create new session
        new_id = uuid4()
        session_data = SessionData()
        db_session = SessionStore(
            id=str(new_id),
            data=json.dumps(session_data.dict())
        )
        self.db.add(db_session)
        self.db.commit()
        
        return new_id, session_data

    async def update_session(self, session_id: UUID, data: SessionData):
        """Update session data"""
        db_session = self.db.query(SessionStore).filter(SessionStore.id == str(session_id)).first()
        if db_session:
            db_session.data = json.dumps(data.dict())
            self.db.commit()

    async def delete_session(self, session_id: UUID):
        """Delete a session"""
        self.db.query(SessionStore).filter(SessionStore.id == str(session_id)).delete()
        self.db.commit()

def attach_session_id(response: Response, session_id: UUID):
    """Attach session ID to response cookie"""
    response.set_cookie(
        key="session_id",
        value=str(session_id),
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax"
    )

def get_session_id(session_id: Optional[str] = Cookie(None)) -> Optional[UUID]:
    """Get session ID from cookie"""
    if session_id:
        try:
            return UUID(session_id)
        except ValueError:
            pass
    return None

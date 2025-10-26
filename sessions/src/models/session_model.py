from datetime import datetime, timedelta
from pydantic import BaseModel

class Session(BaseModel):
    session_id: str
    aes_key: str
    iv: str
    expired_at: datetime
    is_valid: bool = True

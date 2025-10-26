from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import base64
from datetime import datetime
from src.services.rsa_service import get_rsa_service
from src.services.aes_service import get_aes_service, AesKey
from src.services.session_service import get_session_service
import hashlib


def verify_hash(plain_text: str, received_hash: str) -> bool:
    computed_hash = hashlib.sha256(plain_text.encode("utf-8")).hexdigest()
    return computed_hash == received_hash

router = APIRouter(prefix="/api/secure")

# Глобальне сховище для RSA ключів та AES сесій
rsa_keys_store = {}
aes_sessions_store = {}
rsa_id_counter = 1


class SessionRequest(BaseModel):
    session_id: str
    encrypted_aes_key: str
    encrypted_iv: str


class SessionResponse(BaseModel):
    success: bool
    message: str


class EncryptedMessage(BaseModel):
    cipher_text: str
    hash: str



class MessageResponse(BaseModel):
    cipher_text: str


rsa_service = get_rsa_service()
aes_service = get_aes_service()
session_service = get_session_service()


@router.post("/generate-rsa-keys")
def generate_server_rsa_keys():
    """Генерує пару RSA ключів на сервері"""
    global rsa_id_counter
    
    keys = rsa_service.generate_crypto_keys()
    key_id = rsa_id_counter
    rsa_keys_store[key_id] = keys
    rsa_id_counter += 1
    
    return {
        "id": key_id,
        "public_key": base64.b64encode(keys.public_key.encode("utf-8")).decode("utf-8")
    }


EXPIRATION_MINUTES = 1 
@router.post("/establish-session", response_model=SessionResponse)
def establish_session(
    session_data: SessionRequest,
    x_rsa_id: int = Header(...)
):
    """
    Приймає зашифровані AES ключ та IV від клієнта,
    розшифровує їх та зберігає сесію
    """
    if x_rsa_id not in rsa_keys_store:
        raise HTTPException(status_code=404, detail="RSA keys not found")
    
    rsa_keys = rsa_keys_store[x_rsa_id]
    
    try:
        aes_key_str = rsa_service.decrypt(
            rsa_keys.private_key,
            session_data.encrypted_aes_key
        )
        iv_str = rsa_service.decrypt(
            rsa_keys.private_key,
            session_data.encrypted_iv
        )
        expired_at = datetime.now() + timedelta(minutes=EXPIRATION_MINUTES)
        session_service.create_session(
            session_id=session_data.session_id,
            aes_key=aes_key_str,
            iv=iv_str
        )

        
        return SessionResponse(
            success=True,
            message="Session established successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to establish session: {str(e)}")

@router.post("/send-message", response_model=MessageResponse)
def receive_encrypted_message(
    message: EncryptedMessage,
    x_session_id: str = Header(...)
):
    """
    Приймає зашифроване повідомлення від клієнта,
    перевіряє термін дії сесії, розшифровує його,
    додає timestamp та відправляє назад зашифрованим
    """
    if not session_service.validate_session(x_session_id):
        raise HTTPException(status_code=440, detail="Session expired")

    session = session_service.get_session(x_session_id)
    aes_key = AesKey(key=session.aes_key, iv=session.iv)

    try:
        decrypted_message = aes_service.decrypt(aes_key, message.cipher_text)

        if not verify_hash(decrypted_message, message.hash):
            raise HTTPException(status_code=400, detail="Data integrity check failed")


        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        modified_message = f"[Received at {current_time}] {decrypted_message}"

        encrypted_response = aes_service.encrypt(aes_key, modified_message)

        return MessageResponse(cipher_text=encrypted_response)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process message: {str(e)}")

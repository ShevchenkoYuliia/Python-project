from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import base64
from datetime import datetime
from src.services.rsa_service import RsaService
from src.services.aes_service import AesService, AesKey

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


class MessageResponse(BaseModel):
    cipher_text: str


rsa_service = RsaService()
aes_service = AesService()


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
        
        aes_sessions_store[session_data.session_id] = AesKey(
            key=aes_key_str,
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
    розшифровує його, додає timestamp та відправляє назад зашифрованим
    """
    if x_session_id not in aes_sessions_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    aes_key = aes_sessions_store[x_session_id]
    
    try:
        decrypted_message = aes_service.decrypt(aes_key, message.cipher_text)
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        modified_message = f"[Received at {current_time}] {decrypted_message}"
        
        encrypted_response = aes_service.encrypt(aes_key, modified_message)
        
        return MessageResponse(cipher_text=encrypted_response)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process message: {str(e)}")
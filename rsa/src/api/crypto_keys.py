from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.models.rsa_service import RsaService, RsaKeys
import base64

router = APIRouter(prefix="/api")
rsa_service = RsaService()

key_store = {} 
id_counter = 1

class GenerateKeyResponse(BaseModel):
    id: int
    public_key: str
    private_key: str # у реальних застосунках цей ключ не повертається 

class PublicKeyResponse(BaseModel):
    public_key: str

class EncryptRequest(BaseModel):
    public_key_base64: str
    plain_text: str

class EncryptResponse(BaseModel):
    cipher_text: str

class DecryptRequest(BaseModel):
    private_key_base64: str  
    cipher_text: str

class DecryptResponse(BaseModel):
    plain_text: str

@router.post("/generate/rsa-keys", response_model=GenerateKeyResponse)
def generate_rsa_keys():
    ''' Цей ендпоїнт повертає приватний ключ лише з навчальною та тестовою метою 
    для перевірки шифрування/дешифрування у Postman.
    У реальних застосунках приватний ключ ніколи не має залишати сервер.'''
    global id_counter
    try:
        keys = rsa_service.generate_crypto_keys()
        key_id = id_counter
        key_store[key_id] = keys
        id_counter += 1
        return GenerateKeyResponse(
            id=key_id,
            public_key=keys.public_key,
            private_key=keys.private_key
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/rsa-public-key/{key_id}", response_model=PublicKeyResponse)
def get_rsa_public_key(key_id: int):
    keys = key_store.get(key_id)
    if not keys:
        raise HTTPException(status_code=404, detail="Keys not found")
    return PublicKeyResponse(public_key=base64.b64encode(keys.public_key.encode("utf-8")).decode("utf-8"))


@router.post("/encrypt", response_model=EncryptResponse)
def rsa_encrypt(data: EncryptRequest):
    try:
        public_key_pem = base64.b64decode(data.public_key_base64).decode("utf-8")
        cipher_text = rsa_service.encrypt(public_key_pem, data.plain_text)
        return EncryptResponse(cipher_text=cipher_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/decrypt", response_model=DecryptResponse)
def rsa_decrypt(data: DecryptRequest):
    try:
        private_key_pem = base64.b64decode(data.private_key_base64).decode("utf-8")
        plain_text = rsa_service.decrypt(private_key_pem, data.cipher_text)
        return DecryptResponse(plain_text=plain_text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
from dataclasses import dataclass
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend
import base64
import os

@dataclass
class AesKey:
    key: str  
    iv: str  

class AesService:
    def generate_secret_key(self) -> AesKey:
        key = os.urandom(32)  
        iv = os.urandom(16)   # 128-bit IV
        return AesKey(
            key=base64.b64encode(key).decode("utf-8"),
            iv=base64.b64encode(iv).decode("utf-8")
        )

    def encrypt(self, aes_key: AesKey, plain_text: str) -> str:
        key = base64.b64decode(aes_key.key)
        iv = base64.b64decode(aes_key.iv)

        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plain_text.encode("utf-8")) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(ct).decode("utf-8")

    def decrypt(self, aes_key: AesKey, cipher_text: str) -> str:
        key = base64.b64decode(aes_key.key)
        iv = base64.b64decode(aes_key.iv)
        ct = base64.b64decode(cipher_text)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plain = decryptor.update(ct) + decryptor.finalize()

        unpadder = sym_padding.PKCS7(128).unpadder()
        plain = unpadder.update(padded_plain) + unpadder.finalize()

        return plain.decode("utf-8")

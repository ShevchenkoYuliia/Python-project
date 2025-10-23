import requests
import base64
import os
import uuid
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from dataclasses import dataclass
from typing import Optional


@dataclass
class AesKey:
    key: str
    iv: str


@dataclass
class Session:
    session_id: str
    aes_key: AesKey
    rsa_id: int


class SecureClient:
    def __init__(self, server_url: str = "http://localhost:8002"):
        self.server_url = server_url
        self.current_session: Optional[Session] = None
    
    def get_server_public_key(self) -> tuple[int, str]:
        """Отримує публічний ключ з серверу"""
        print(f"\n[CLIENT] Запит публічного ключа з серверу: {self.server_url}...")
        response = requests.post(f"{self.server_url}/api/secure/generate-rsa-keys")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get public key: {response.text}")
        
        data = response.json()
        rsa_id = data["id"]
        public_key_b64 = data["public_key"]
        
        print(f"[CLIENT] Отримано публічний ключ (RSA ID: {rsa_id})")
        return rsa_id, public_key_b64
    
    def generate_aes_key(self) -> AesKey:
        """Генерує таємний ключ та IV для AES"""
        print("[CLIENT] Генерація таємного ключа та вектора ініціалізації...")
        key = os.urandom(32)
        iv = os.urandom(16)  
        
        aes_key = AesKey(
            key=base64.b64encode(key).decode("utf-8"),
            iv=base64.b64encode(iv).decode("utf-8")
        )
        print("[CLIENT] Таємний ключ згенеровано")
        return aes_key
    
    def encrypt_with_rsa(self, public_key_b64: str, plain_text: str) -> str:
        """Шифрує текст публічним ключем RSA"""
        public_key_pem = base64.b64decode(public_key_b64).decode("utf-8")
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        
        cipher_text = public_key.encrypt(
            plain_text.encode("utf-8"),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(cipher_text).decode("utf-8")
    
    def establish_session(self, rsa_id: int, public_key_b64: str, aes_key: AesKey) -> str:
        """Встановлює безпечну сесію з сервером"""
        session_id = str(uuid.uuid4())
        print(f"\n[CLIENT] Створення сесії (Session ID: {session_id})...")
        
        print("[CLIENT] Шифрування таємного ключа публічним ключем RSA...")
        encrypted_key = self.encrypt_with_rsa(public_key_b64, aes_key.key)
        encrypted_iv = self.encrypt_with_rsa(public_key_b64, aes_key.iv)
        
        print("[CLIENT] Відправка зашифрованих даних на сервер...")
        response = requests.post(
            f"{self.server_url}/api/secure/establish-session",
            json={
                "session_id": session_id,
                "encrypted_aes_key": encrypted_key,
                "encrypted_iv": encrypted_iv
            },
            headers={
                "x-rsa-id": str(rsa_id)
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to establish session: {response.text}")
        
        result = response.json()
        print(f"[CLIENT] ✓ {result['message']}")
        
        return session_id
    
    def encrypt_aes(self, aes_key: AesKey, plain_text: str) -> str:
        """Шифрує повідомлення за допомогою AES"""
        key = base64.b64decode(aes_key.key)
        iv = base64.b64decode(aes_key.iv)
        
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plain_text.encode("utf-8")) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(ct).decode("utf-8")
    
    def decrypt_aes(self, aes_key: AesKey, cipher_text: str) -> str:
        """Розшифровує повідомлення за допомогою AES"""
        key = base64.b64decode(aes_key.key)
        iv = base64.b64decode(aes_key.iv)
        ct = base64.b64decode(cipher_text)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plain = decryptor.update(ct) + decryptor.finalize()
        
        unpadder = sym_padding.PKCS7(128).unpadder()
        plain = unpadder.update(padded_plain) + unpadder.finalize()
        
        return plain.decode("utf-8")
    
    def send_encrypted_message(self, message: str):
        """Відправляє зашифроване повідомлення на сервер"""
        if not self.current_session:
            raise Exception("No active session. Please establish a session first.")
        
        print(f"\n[CLIENT] Шифрування повідомлення таємним ключем...")
        encrypted_message = self.encrypt_aes(self.current_session.aes_key, message)
        
        print(f"[CLIENT] Відправка зашифрованого повідомлення на сервер...")
        response = requests.post(
            f"{self.server_url}/api/secure/send-message",
            json={
                "cipher_text": encrypted_message
            },
            headers={
                "x-session-id": self.current_session.session_id
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to send message: {response.text}")
        
        result = response.json()
        encrypted_response = result["cipher_text"]
        
        print(f"[CLIENT] Отримано відповідь від серверу, дешифрування...")
        decrypted_response = self.decrypt_aes(
            self.current_session.aes_key,
            encrypted_response
        )
        
        return decrypted_response
    
    def start_secure_communication(self):
        """Головний метод для початку безпечної комунікації"""
        print("=" * 60)
        print("    SECURE COMMUNICATION CLIENT")
        print("=" * 60)
        
        try:
            rsa_id, public_key_b64 = self.get_server_public_key()
            
            aes_key = self.generate_aes_key()
            
            session_id = self.establish_session(rsa_id, public_key_b64, aes_key)
            
            self.current_session = Session(
                session_id=session_id,
                aes_key=aes_key,
                rsa_id=rsa_id
            )
            
            print("\n" + "=" * 60)
            print("    ✓ БЕЗПЕЧНИЙ КАНАЛ ВСТАНОВЛЕНО")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Помилка: {e}")
            return
        
        while True:
            print("\n" + "-" * 60)
            user_message = input("Введіть повідомлення (або 'exit' для виходу): ").strip()
            
            if user_message.lower() == 'exit':
                print("\nЗавершення роботи клієнта...")
                break
            
            if not user_message:
                print("⚠️  Повідомлення не може бути порожнім")
                continue
            
            try:
                response = self.send_encrypted_message(user_message)
                
                print("\n" + "=" * 60)
                print("    📩 ВІДПОВІДЬ ВІД СЕРВЕРУ:")
                print("=" * 60)
                print(f"\n{response}\n")
                print(f"Session ID: {self.current_session.session_id}")
                print("=" * 60)
                
            except Exception as e:
                print(f"\n❌ Помилка при відправці повідомлення: {e}")


def main():
    client = SecureClient(server_url="http://localhost:8002")
    client.start_secure_communication()


if __name__ == "__main__":
    main()
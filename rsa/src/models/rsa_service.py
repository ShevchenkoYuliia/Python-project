from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import base64

@dataclass
class RsaKeys:
    public_key: str
    private_key: str

class RsaService:
    def generate_crypto_keys(self) -> RsaKeys:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        return RsaKeys(public_key=public_pem, private_key=private_pem)

    def encrypt(self, public_key_pem: str, plain_text: str) -> str:
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

    def decrypt(self, private_key_pem: str, cipher_text_b64: str) -> str:
        private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        cipher_bytes = base64.b64decode(cipher_text_b64)
        plain_bytes = private_key.decrypt(
            cipher_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plain_bytes.decode("utf-8")

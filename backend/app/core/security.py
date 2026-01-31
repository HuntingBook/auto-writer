import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _derive_key(secret: str) -> bytes:
  raw = secret.encode("utf-8")
  if len(raw) >= 32:
    return raw[:32]
  return (raw + (b"0" * 32))[:32]


def encrypt_text(secret: str, plaintext: str) -> str:
  key = _derive_key(secret)
  nonce = os.urandom(12)
  aes = AESGCM(key)
  ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
  return base64.urlsafe_b64encode(nonce + ct).decode("utf-8")


def decrypt_text(secret: str, token: str) -> str:
  raw = base64.urlsafe_b64decode(token.encode("utf-8"))
  nonce, ct = raw[:12], raw[12:]
  aes = AESGCM(_derive_key(secret))
  pt = aes.decrypt(nonce, ct, None)
  return pt.decode("utf-8")

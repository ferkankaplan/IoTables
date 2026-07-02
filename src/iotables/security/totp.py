import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet

TOTP_DIGITS = 6
TOTP_INTERVAL_SECONDS = 30
TOTP_SECRET_BYTES = 20


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(TOTP_SECRET_BYTES)).decode("ascii").rstrip("=")


def build_otpauth_url(*, issuer: str, username: str, secret: str) -> str:
    label = quote(f"{issuer}:{username}")
    issuer_param = quote(issuer)
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer_param}&digits=6&period=30"


def verify_totp_code(secret: str, code: str, *, now: int | None = None) -> bool:
    normalized_code = code.strip()
    if not normalized_code.isdigit() or len(normalized_code) != TOTP_DIGITS:
        return False

    current_counter = int((now if now is not None else time.time()) // TOTP_INTERVAL_SECONDS)
    for counter in range(current_counter - 1, current_counter + 2):
        if hmac.compare_digest(generate_totp_code(secret, counter), normalized_code):
            return True
    return False


def generate_totp_code(secret: str, counter: int) -> str:
    key = decode_base32_secret(secret)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(truncated % (10**TOTP_DIGITS)).zfill(TOTP_DIGITS)


def encrypt_totp_secret(secret: str, encryption_key: str) -> bytes:
    return fernet(encryption_key).encrypt(secret.encode("utf-8"))


def decrypt_totp_secret(secret_ciphertext: bytes, encryption_key: str) -> str:
    return fernet(encryption_key).decrypt(secret_ciphertext).decode("utf-8")


def fernet(encryption_key: str) -> Fernet:
    digest = hashlib.sha256(encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def decode_base32_secret(secret: str) -> bytes:
    padding = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode((secret + padding).upper())

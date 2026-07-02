import base64
import hashlib
import hmac
import secrets

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 390_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return "pbkdf2_sha256${iterations}${salt}${digest}".format(
        iterations=PBKDF2_ITERATIONS,
        salt=base64.urlsafe_b64encode(salt).decode("ascii"),
        digest=base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False

        salt_bytes = base64.urlsafe_b64decode(salt.encode("ascii"))
        expected_digest_bytes = base64.urlsafe_b64decode(expected_digest.encode("ascii"))
        actual_digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            salt_bytes,
            int(iterations),
        )
    except ValueError, TypeError:
        return False

    return hmac.compare_digest(actual_digest, expected_digest_bytes)

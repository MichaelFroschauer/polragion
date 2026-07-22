from cryptography.fernet import Fernet


class TokenCipher:
    def __init__(self, key: str):
        try:
            self._fernet = Fernet(key.strip().encode())
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "TOKEN_ENCRYPTION_KEY is not a valid Fernet key. "
                "Generate one with Fernet.generate_key()."
            ) from exc

    def encrypt(self, token: str) -> str:
        return self._fernet.encrypt(token.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        return self._fernet.decrypt(encrypted_token.encode()).decode()

"""zeroFIR configuration.

All settings live in .env with the ZFIR_ prefix. JWT_SECRET is
REQUIRED — the process refuses to start if it's missing, the default
placeholder, or shorter than 32 chars (CyberFraud lesson, applied
from day one)."""
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


_DEFAULT_JWT_SECRET = "REPLACE-ME-WITH-64-CHAR-HEX"
_JWT_MIN_LENGTH = 32


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "zerofir"

    # ── JWT ─────────────────────────────────────────────────────────
    JWT_SECRET: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480       # 8 hours

    # ── CORS ────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173"

    # ── Docs ────────────────────────────────────────────────────────
    DISABLE_DOCS: bool = False

    # ── NCRP integration (API 1) ────────────────────────────────────
    # Shared static API key. NCRP sends `X-API-Key: <key>` on POST
    # /api/v1/ncrp/complaints. Empty string DISABLES the endpoint
    # (returns 503) so the receiver never runs unauthenticated. On
    # prod, set this to a strong random value and rotate via .env.
    NCRP_API_KEY: str = ""

    class Config:
        env_prefix = "ZFIR_"
        env_file = ".env"

    @property
    def database_url(self) -> str:
        # URL-encode the password so `@` in it (Sandy@411 style) doesn't
        # get parsed as the user/host separator. CyberFraud lesson.
        pwd = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+asyncmy://{self.DB_USER}:{pwd}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()

# Fail-loud on a weak JWT secret. Never ship with a default value.
if settings.JWT_SECRET == _DEFAULT_JWT_SECRET:
    raise RuntimeError(
        "ZFIR_JWT_SECRET is using the placeholder default. "
        "Set it in .env to a strong random value before starting the backend. "
        "Generate one with:  openssl rand -hex 32"
    )
if len(settings.JWT_SECRET) < _JWT_MIN_LENGTH:
    raise RuntimeError(
        f"ZFIR_JWT_SECRET is too short ({len(settings.JWT_SECRET)} chars). "
        f"Minimum {_JWT_MIN_LENGTH} characters. "
        f"Generate a stronger one with:  openssl rand -hex 32"
    )

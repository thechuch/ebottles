import hmac
from typing import Optional

from fastapi import Header, HTTPException

from app.config import get_settings


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-KEY")) -> None:
    """Optional API key gate.

    If `Settings.api_key` is set (non-empty), require `X-API-KEY` header.
    """
    settings = get_settings()
    expected = (settings.api_key or "").strip()
    if not expected:
        return
    provided = (x_api_key or "").strip()
    if not provided or not constant_time_equals(provided, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")



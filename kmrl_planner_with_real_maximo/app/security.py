# app/security.py
import os
from fastapi import HTTPException, Request

DEFAULT_ADMIN_API_KEY = "kmrl-admin-secret"


def require_admin_key(request: Request):
    """Simple API-key auth for admin endpoints.

    The expected key comes from the ADMIN_API_KEY environment variable
    (defaults to a dev-only value). Scale up to real auth for production.
    """
    expected = os.getenv("ADMIN_API_KEY", DEFAULT_ADMIN_API_KEY)
    provided = request.headers.get("X-API-Key", "")
    if provided != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True
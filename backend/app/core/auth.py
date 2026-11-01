"""Authentication helpers for browser-facing API routes.

Local development remains simple by leaving ``REQUIRE_FIREBASE_AUTH`` false.
Production sets it true and sends Firebase ID tokens from the signed-in browser.
"""

from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status

from app.core.config import get_settings


@lru_cache
def _firebase_app():
    """Initialize Firebase Admin with application-default credentials.

    On Cloud Run this uses the attached service account, avoiding a downloaded
    service-account key. A local developer may instead use application-default
    credentials when testing the production authentication path.
    """
    settings = get_settings()
    if not settings.firebase_project_id:
        raise RuntimeError("FIREBASE_PROJECT_ID must be set when Firebase authentication is required.")

    try:
        import firebase_admin
    except ImportError as exc:  # pragma: no cover - checked in deployment builds
        raise RuntimeError("firebase-admin must be installed when Firebase authentication is required.") from exc

    try:
        return firebase_admin.get_app()
    except ValueError:
        return firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})


def verify_bearer_token(authorization: str | None) -> dict[str, Any]:
    """Validate a Firebase ID token and return its decoded claims.

    The caller receives only a generic 401 response, never the provider's
    detailed token error.
    """
    settings = get_settings()
    if not settings.require_firebase_auth:
        return {}

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firebase sign-in is required.")

    try:
        from firebase_admin import auth

        return auth.verify_id_token(token, app=_firebase_app(), check_revoked=True)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Firebase session.") from exc

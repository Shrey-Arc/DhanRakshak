from __future__ import annotations

import jwt
import httpx
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.config import get_settings
from app.services.supabase_client import get_supabase_client


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str | None = None
    full_name: str | None = None
    is_admin: bool = False


async def _validate_with_supabase(token: str) -> dict:
    settings = get_settings()
    if not settings.supabase_anon_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing anon key")
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.supabase_url}/auth/v1/user", headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return response.json()


async def get_current_user(request: Request) -> AuthenticatedUser:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = auth_header.split(" ", 1)[1]
    settings = get_settings()
    payload = None
    if settings.jwt_secret:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    else:
        payload = await _validate_with_supabase(token)
    user_id = payload.get("sub") or payload.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = AuthenticatedUser(
        user_id=user_id,
        email=payload.get("email"),
        full_name=payload.get("user_metadata", {}).get("full_name") if isinstance(payload.get("user_metadata"), dict) else None,
        is_admin=payload.get("app_metadata", {}).get("role") == "admin",
    )
    return user


async def get_admin_user(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


async def ensure_user_record(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    client = get_supabase_client()
    client.ensure_user(user)
    return user

from fastapi import APIRouter, Depends

from app.auth import AuthenticatedUser, ensure_user_record
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/init")
async def init_user(user: AuthenticatedUser = Depends(ensure_user_record)) -> dict:
    client = get_supabase_client()
    client.insert_audit(user.user_id, "USER_LOGIN", {"email": user.email})
    return {"user_id": user.user_id, "email": user.email}

from fastapi import APIRouter, Depends

from app.auth import AuthenticatedUser, get_admin_user
from app.models import AuditLogResponse
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditLogResponse)
async def list_audit_logs(
    user: AuthenticatedUser = Depends(get_admin_user),
) -> AuditLogResponse:
    client = get_supabase_client()
    logs = client.list_audit_logs()
    return AuditLogResponse(logs=logs)

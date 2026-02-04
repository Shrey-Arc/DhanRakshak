from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthenticatedUser, ensure_user_record
from app.config import get_settings
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/download/{filing_id}")
async def download_report(
    filing_id: str,
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> dict:
    settings = get_settings()
    client = get_supabase_client()
    dossier_path = f"{filing_id}/dossier.zip"
    try:
        signed_url = client.create_signed_url(settings.dossier_bucket, dossier_path, expires_in=3600)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier not found") from exc
    return {"signed_url": signed_url}

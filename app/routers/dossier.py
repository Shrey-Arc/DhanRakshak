from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthenticatedUser, ensure_user_record
from app.config import get_settings
from app.models import GenerateDossierRequest
from app.services.dossier import build_dossier
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="", tags=["dossier"])


@router.post("/generate-dossier")
async def generate_dossier(
    payload: GenerateDossierRequest,
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> dict:
    client = get_supabase_client()
    settings = get_settings()
    filing = client.get_filing(payload.filing_id, user.user_id)
    if not filing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filing not found")
    if filing.get("status") != "FINAL":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filing not finalized")

    blockchain_record = client.get_blockchain_record(payload.filing_id, user.user_id)
    if not blockchain_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Blockchain record missing")

    documents = client.get_documents(payload.filing_id, user.user_id)
    if not documents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Form-16 required")

    form16_doc = documents[0]
    form16_bytes = client.download_file(settings.storage_bucket, form16_doc["storage_path"])

    summary_data = {
        "filing_id": payload.filing_id,
        "status": filing.get("status"),
    }

    full_name = filing.get("metadata", {}).get("full_name") or user.full_name or "Unknown"
    dossier_bytes = build_dossier(form16_bytes, summary_data, full_name, blockchain_record["tx_hash"])
    dossier_path = client.store_dossier(settings.dossier_bucket, payload.filing_id, dossier_bytes)
    client.insert_audit(user.user_id, "DOSSIER_GENERATED", {"filing_id": payload.filing_id})

    signed_url = client.create_signed_url(settings.dossier_bucket, dossier_path, expires_in=3600)
    return {"dossier_path": dossier_path, "signed_url": signed_url}

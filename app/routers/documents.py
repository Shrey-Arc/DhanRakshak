from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth import AuthenticatedUser, ensure_user_record
from app.config import get_settings
from app.models import UploadDocumentResponse
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf", "image/png", "image/jpeg"}


@router.post("/upload", response_model=UploadDocumentResponse)
async def upload_document(
    filing_id: str,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> UploadDocumentResponse:
    settings = get_settings()
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")
    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

    client = get_supabase_client()
    storage_path = f"{user.user_id}/{filing_id}/form16.pdf"
    client.upload_file(settings.storage_bucket, storage_path, content, file.content_type)
    document = client.insert_document(filing_id, user.user_id, storage_path, file.content_type)
    client.update_filing_status(filing_id, user.user_id, "DOCUMENT_UPLOADED")
    client.insert_audit(user.user_id, "FORM16_UPLOADED", {"filing_id": filing_id, "document_id": document["id"]})
    return UploadDocumentResponse(document_id=document["id"], storage_path=storage_path)

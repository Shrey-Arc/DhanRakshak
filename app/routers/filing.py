from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthenticatedUser, ensure_user_record
from app.models import FilingCreateRequest, FilingDetailResponse, FilingResponse
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="/filing", tags=["filing"])


@router.post("/create", response_model=FilingResponse)
async def create_filing(
    payload: FilingCreateRequest,
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> FilingResponse:
    client = get_supabase_client()
    filing = client.create_filing(user, payload.metadata)
    client.insert_audit(user.user_id, "FILING_CREATED", {"filing_id": filing["id"]})
    return FilingResponse(id=filing["id"], status=filing["status"], metadata=filing.get("metadata", {}))


@router.get("/{filing_id}", response_model=FilingDetailResponse)
async def get_filing(
    filing_id: str,
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> FilingDetailResponse:
    client = get_supabase_client()
    filing = client.get_filing(filing_id, user.user_id)
    if not filing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filing not found")
    return FilingDetailResponse(
        filing={k: v for k, v in filing.items() if k not in {"documents", "ml_results", "risk_flags"}},
        documents=filing.get("documents", []),
        ml_results=filing.get("ml_results", None),
        risk_flags=filing.get("risk_flags", None),
    )

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthenticatedUser, ensure_user_record
from app.models import MLResultRequest
from app.services.supabase_client import get_supabase_client

router = APIRouter(prefix="", tags=["ml"])


@router.post("/ml-results")
async def ingest_ml_results(
    payload: MLResultRequest,
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> dict:
    client = get_supabase_client()
    if payload.risk_flags:
        invalid = {value for value in payload.risk_flags.values() if value not in {"green", "yellow"}}
        if invalid:
            raise HTTPException(\n                status_code=status.HTTP_400_BAD_REQUEST,\n                detail=\"Risk flags must be green or yellow\",\n            )
    ml_result = client.insert_ml_results(payload.filing_id, user.user_id, payload.parsed_json)
    if payload.risk_flags:
        client.upsert_risk_flags(payload.filing_id, user.user_id, payload.risk_flags)
    client.update_filing_status(payload.filing_id, user.user_id, "ML_PARSED")
    client.insert_audit(user.user_id, "ML_RESULT_RECEIVED", {"filing_id": payload.filing_id})
    return {"ml_result_id": ml_result["id"]}

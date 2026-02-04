from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthenticatedUser, ensure_user_record
from app.models import FinalizeRequest
from app.services import blockchain
from app.services.supabase_client import get_supabase_client
from app.services.transactions import finalize_filing_transaction

router = APIRouter(prefix="", tags=["finalize"])


@router.post("/finalize")
async def finalize_filing(
    payload: FinalizeRequest,
    user: AuthenticatedUser = Depends(ensure_user_record),
) -> dict:
    client = get_supabase_client()
    filing = client.get_filing(payload.filing_id, user.user_id)
    if not filing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filing not found")

    documents = client.get_documents(payload.filing_id, user.user_id)
    if not documents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Form-16 required")

    ml_result = client.get_ml_result(payload.filing_id, user.user_id)
    if not ml_result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ML results required")

    payload_hash = blockchain.canonical_hash(
        {
            "filing": {k: v for k, v in filing.items() if k not in {"documents", "ml_results", "risk_flags"}},
            "documents": documents,
            "ml_results": ml_result,
        }
    )
    tx_hash = blockchain.send_to_blockchain(payload_hash)

    try:
        finalize_filing_transaction(payload.filing_id, user.user_id, tx_hash, payload_hash)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    client.insert_audit(user.user_id, "BLOCKCHAIN_WRITTEN", {"filing_id": payload.filing_id, "tx_hash": tx_hash})
    client.insert_audit(user.user_id, "FINALIZED", {"filing_id": payload.filing_id})

    return {"tx_hash": tx_hash, "payload_hash": payload_hash}

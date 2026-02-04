from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class FilingCreateRequest(BaseModel):
    metadata: dict[str, Any] | None = None


class FilingResponse(BaseModel):
    id: str
    status: str
    metadata: dict[str, Any]


class UploadDocumentResponse(BaseModel):
    document_id: str
    storage_path: str


class MLResultRequest(BaseModel):
    filing_id: str
    parsed_json: dict[str, Any]
    risk_flags: dict[str, str] | None = None


class FinalizeRequest(BaseModel):
    filing_id: str


class GenerateDossierRequest(BaseModel):
    filing_id: str


class FilingDetailResponse(BaseModel):
    filing: dict[str, Any]
    documents: list[dict[str, Any]]
    ml_results: dict[str, Any] | None
    risk_flags: dict[str, Any] | None


class AuditLogResponse(BaseModel):
    logs: list[dict[str, Any]] = Field(default_factory=list)

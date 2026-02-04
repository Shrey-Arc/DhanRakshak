from __future__ import annotations

import io
import json
import uuid
from datetime import datetime
from typing import Any

from supabase import create_client, Client

from app.config import get_settings
from app.auth import AuthenticatedUser


class SupabaseService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    def ensure_user(self, user: AuthenticatedUser) -> None:
        existing = self.client.table("users").select("id").eq("id", user.user_id).execute()
        if not existing.data:
            self.client.table("users").insert(
                {
                    "id": user.user_id,
                    "email": user.email,
                    "full_name": user.full_name,
                }
            ).execute()

    def create_filing(self, user: AuthenticatedUser, metadata: dict[str, Any] | None) -> dict[str, Any]:
        payload = {
            "user_id": user.user_id,
            "status": "DRAFT",
            "metadata": metadata or {},
        }
        response = self.client.table("filings").insert(payload).execute()
        return response.data[0]

    def insert_document(self, filing_id: str, user_id: str, storage_path: str, content_type: str) -> dict[str, Any]:
        response = self.client.table("documents").insert(
            {
                "filing_id": filing_id,
                "user_id": user_id,
                "document_type": "FORM16",
                "storage_path": storage_path,
                "content_type": content_type,
            }
        ).execute()
        return response.data[0]

    def insert_ml_results(self, filing_id: str, user_id: str, parsed_json: dict[str, Any]) -> dict[str, Any]:
        response = self.client.table("ml_results").insert(
            {
                "filing_id": filing_id,
                "user_id": user_id,
                "parsed_json": parsed_json,
            }
        ).execute()
        return response.data[0]

    def upsert_risk_flags(self, filing_id: str, user_id: str, flags: dict[str, str]) -> dict[str, Any]:
        response = self.client.table("risk_flags").upsert(
            {
                "filing_id": filing_id,
                "user_id": user_id,
                "flags": flags,
            },
            on_conflict="filing_id",
        ).execute()
        return response.data[0]

    def get_filing(self, filing_id: str, user_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("filings")
            .select("*, documents(*), ml_results(*), risk_flags(*)")
            .eq("id", filing_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def update_filing_status(self, filing_id: str, user_id: str, status: str) -> None:
        self.client.table("filings").update({"status": status}).eq("id", filing_id).eq("user_id", user_id).execute()

    def insert_audit(self, user_id: str, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        self.client.table("audit_logs").insert(
            {
                "user_id": user_id,
                "event_type": event_type,
                "metadata": metadata or {},
            }
        ).execute()

    def list_audit_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        response = self.client.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data

    def upload_file(self, bucket: str, storage_path: str, content: bytes, content_type: str) -> None:
        self.client.storage.from_(bucket).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": True},
        )

    def download_file(self, bucket: str, storage_path: str) -> bytes:
        return self.client.storage.from_(bucket).download(storage_path)

    def create_signed_url(self, bucket: str, storage_path: str, expires_in: int = 3600) -> str:
        response = self.client.storage.from_(bucket).create_signed_url(storage_path, expires_in)
        return response.get("signedURL")

    def store_dossier(self, bucket: str, filing_id: str, content: bytes) -> str:
        dossier_path = f"{filing_id}/dossier.zip"
        self.upload_file(bucket, dossier_path, content, "application/zip")
        return dossier_path

    def get_documents(self, filing_id: str, user_id: str) -> list[dict[str, Any]]:
        response = (
            self.client.table("documents")
            .select("*")
            .eq("filing_id", filing_id)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data

    def get_ml_result(self, filing_id: str, user_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("ml_results")
            .select("*")
            .eq("filing_id", filing_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def get_risk_flags(self, filing_id: str, user_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("risk_flags")
            .select("*")
            .eq("filing_id", filing_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def record_blockchain(self, filing_id: str, user_id: str, tx_hash: str, payload_hash: str) -> dict[str, Any]:
        response = self.client.table("blockchain_records").insert(
            {
                "filing_id": filing_id,
                "user_id": user_id,
                "tx_hash": tx_hash,
                "payload_hash": payload_hash,
            }
        ).execute()
        return response.data[0]

    def get_blockchain_record(self, filing_id: str, user_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("blockchain_records")
            .select("*")
            .eq("filing_id", filing_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return response.data


_supabase_service: SupabaseService | None = None


def get_supabase_client() -> SupabaseService:
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service

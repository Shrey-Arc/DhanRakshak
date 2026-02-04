from __future__ import annotations

from typing import Any
import json

import psycopg2
from psycopg2.extras import Json

from app.config import get_settings


def finalize_filing_transaction(
    filing_id: str,
    user_id: str,
    tx_hash: str,
    payload_hash: str,
) -> None:
    settings = get_settings()
    if not settings.supabase_db_url:
        raise RuntimeError("SUPABASE_DB_URL required for transactional finalize")

    with psycopg2.connect(settings.supabase_db_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM filings WHERE id = %s AND user_id = %s FOR UPDATE",
                (filing_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Filing not found")
            if row[0] == "FINAL":
                raise ValueError("Filing already finalized")

            cursor.execute(
                "INSERT INTO blockchain_records (filing_id, user_id, tx_hash, payload_hash) VALUES (%s, %s, %s, %s)",
                (filing_id, user_id, tx_hash, payload_hash),
            )
            cursor.execute(
                "UPDATE filings SET status = 'FINAL' WHERE id = %s AND user_id = %s",
                (filing_id, user_id),
            )
        conn.commit()

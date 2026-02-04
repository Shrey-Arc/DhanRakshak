import io
import os
import jwt
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.services import supabase_client
from app.services import transactions
from app.services import blockchain


class FakeSupabase:
    def __init__(self) -> None:
        self.users = {}
        self.filings = {}
        self.documents = {}
        self.ml_results = {}
        self.risk_flags = {}
        self.blockchain = {}
        self.audit_logs = []
        self.storage = {}

    def ensure_user(self, user):
        self.users[user.user_id] = {"id": user.user_id, "email": user.email, "full_name": user.full_name}

    def create_filing(self, user, metadata):
        filing_id = str(uuid.uuid4())
        filing = {"id": filing_id, "user_id": user.user_id, "status": "DRAFT", "metadata": metadata or {}}
        self.filings[filing_id] = filing
        return filing

    def insert_document(self, filing_id, user_id, storage_path, content_type):
        doc_id = str(uuid.uuid4())
        doc = {
            "id": doc_id,
            "filing_id": filing_id,
            "user_id": user_id,
            "storage_path": storage_path,
            "content_type": content_type,
        }
        self.documents.setdefault(filing_id, []).append(doc)
        return doc

    def insert_ml_results(self, filing_id, user_id, parsed_json):
        ml_id = str(uuid.uuid4())
        ml = {"id": ml_id, "filing_id": filing_id, "user_id": user_id, "parsed_json": parsed_json}
        self.ml_results[filing_id] = ml
        return ml

    def upsert_risk_flags(self, filing_id, user_id, flags):
        entry = {"id": str(uuid.uuid4()), "filing_id": filing_id, "user_id": user_id, "flags": flags}
        self.risk_flags[filing_id] = entry
        return entry

    def get_filing(self, filing_id, user_id):
        filing = self.filings.get(filing_id)
        if not filing or filing["user_id"] != user_id:
            return None
        return {
            **filing,
            "documents": self.documents.get(filing_id, []),
            "ml_results": self.ml_results.get(filing_id),
            "risk_flags": self.risk_flags.get(filing_id),
        }

    def update_filing_status(self, filing_id, user_id, status):
        self.filings[filing_id]["status"] = status

    def insert_audit(self, user_id, event_type, metadata=None):
        self.audit_logs.append({"user_id": user_id, "event_type": event_type, "metadata": metadata or {}})

    def list_audit_logs(self, limit=100):
        return list(reversed(self.audit_logs))[:limit]

    def upload_file(self, bucket, storage_path, content, content_type):
        self.storage[(bucket, storage_path)] = content

    def download_file(self, bucket, storage_path):
        return self.storage[(bucket, storage_path)]

    def create_signed_url(self, bucket, storage_path, expires_in=3600):
        return f"https://example.com/{bucket}/{storage_path}?exp={expires_in}"

    def store_dossier(self, bucket, filing_id, content):
        path = f"{filing_id}/dossier.zip"
        self.upload_file(bucket, path, content, "application/zip")
        return path

    def get_documents(self, filing_id, user_id):
        return self.documents.get(filing_id, [])

    def get_ml_result(self, filing_id, user_id):
        return self.ml_results.get(filing_id)

    def get_risk_flags(self, filing_id, user_id):
        return self.risk_flags.get(filing_id)

    def get_blockchain_record(self, filing_id, user_id):
        return self.blockchain.get(filing_id)

    def record_blockchain(self, filing_id, user_id, tx_hash, payload_hash):
        entry = {"filing_id": filing_id, "user_id": user_id, "tx_hash": tx_hash, "payload_hash": payload_hash}
        self.blockchain[filing_id] = entry
        return entry


def test_happy_path(monkeypatch):
    os.environ["SUPABASE_URL"] = "https://example.supabase.co"
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "service-key"
    os.environ["JWT_SECRET"] = "secret"
    os.environ["SUPABASE_DB_URL"] = "postgresql://user:pass@localhost/db"

    fake = FakeSupabase()
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: fake)

    def fake_finalize(filing_id, user_id, tx_hash, payload_hash):
        fake.record_blockchain(filing_id, user_id, tx_hash, payload_hash)
        fake.update_filing_status(filing_id, user_id, "FINAL")

    monkeypatch.setattr(transactions, "finalize_filing_transaction", fake_finalize)
    monkeypatch.setattr(blockchain, "send_to_blockchain", lambda payload_hash: "SIMULATED_TX_TEST")

    token = jwt.encode({"sub": "user-123", "email": "user@example.com"}, "secret", algorithm="HS256")
    client = TestClient(app)

    response = client.post("/filing/create", json={"metadata": {"full_name": "Jane Doe"}}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    filing_id = response.json()["id"]

    file_bytes = io.BytesIO(b"%PDF-1.4 test")
    response = client.post(
        f"/documents/upload?filing_id={filing_id}",
        files={"file": ("form16.pdf", file_bytes, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    response = client.post(
        "/ml-results",
        json={"filing_id": filing_id, "parsed_json": {"income": 100}, "risk_flags": {"income": "green"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    response = client.post(
        "/finalize",
        json={"filing_id": filing_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    response = client.post(
        "/generate-dossier",
        json={"filing_id": filing_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "signed_url" in response.json()

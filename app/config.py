import os
from functools import lru_cache
from pydantic import BaseModel, AnyUrl


class Settings(BaseModel):
    supabase_url: AnyUrl
    supabase_service_role_key: str
    supabase_anon_key: str | None = None
    jwt_secret: str | None = None
    blockchain_rpc: str | None = None
    contract_address: str | None = None
    supabase_db_url: str | None = None
    storage_bucket: str = "filings"
    dossier_bucket: str = "dossiers"
    max_upload_mb: int = 10
    enable_admin_audit: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_service_role_key=os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
        jwt_secret=os.getenv("JWT_SECRET"),
        blockchain_rpc=os.getenv("BLOCKCHAIN_RPC"),
        contract_address=os.getenv("CONTRACT_ADDRESS"),
        supabase_db_url=os.getenv("SUPABASE_DB_URL"),
        storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "filings"),
        dossier_bucket=os.getenv("SUPABASE_DOSSIER_BUCKET", "dossiers"),
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        enable_admin_audit=os.getenv("ENABLE_ADMIN_AUDIT", "true").lower() == "true",
    )

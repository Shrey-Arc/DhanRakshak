# DhanRakshak Backend

Production-ready FastAPI backend for DhanRakshak filings.

## Features
- Supabase Postgres + Storage integration
- JWT validation via Supabase or local secret
- Filing lifecycle with ML results ingestion
- Blockchain hash stub with optional JSON-RPC
- Dossier ZIP generation (form16, summary, heatmap, certificate)
- Audit logging and admin audit endpoint

## Storage Conventions
- Form-16 upload: `filings/<user_id>/<filing_id>/form16.pdf`
- Dossier zip: `dossiers/<filing_id>/dossier.zip`

## Environment Variables (Render)
Set these in Render dashboard:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `JWT_SECRET` (optional if validating via Supabase)
- `SUPABASE_DB_URL` (required for transactional finalize)
- `BLOCKCHAIN_RPC` (optional)
- `CONTRACT_ADDRESS` (optional)
- `BLOCKCHAIN_PRIVATE_KEY` (optional)
- `SUPABASE_STORAGE_BUCKET` (default `filings`)
- `SUPABASE_DOSSIER_BUCKET` (default `dossiers`)
- `MAX_UPLOAD_MB` (default `10`)
- `ENABLE_ADMIN_AUDIT` (default `true`)

## Render Deployment
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Build command: `pip install -r requirements.txt`

## JWT Verification Snippet
The service validates JWTs via local secret if `JWT_SECRET` is set; otherwise it calls Supabase `/auth/v1/user` using the anon key.

```python
payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
```

## Signed URL Example
```python
signed_url = client.create_signed_url("filings", "<path>", expires_in=3600)
```

## Example cURL Requests

### Upload Form-16
```bash
curl -X POST "$BASE_URL/documents/upload?filing_id=$FILING_ID" \
  -H "Authorization: Bearer $SUPABASE_JWT" \
  -F "file=@form16.pdf"
```

### Send ML Results
```bash
curl -X POST "$BASE_URL/ml-results" \
  -H "Authorization: Bearer $SUPABASE_JWT" \
  -H "Content-Type: application/json" \
  -d '{"filing_id":"'$FILING_ID'","parsed_json":{"income":1234},"risk_flags":{"income":"green"}}'
```

### Finalize Filing
```bash
curl -X POST "$BASE_URL/finalize" \
  -H "Authorization: Bearer $SUPABASE_JWT" \
  -H "Content-Type: application/json" \
  -d '{"filing_id":"'$FILING_ID'"}'
```

### Generate Dossier
```bash
curl -X POST "$BASE_URL/generate-dossier" \
  -H "Authorization: Bearer $SUPABASE_JWT" \
  -H "Content-Type: application/json" \
  -d '{"filing_id":"'$FILING_ID'"}'
```

## SQL Schema & RLS
Use the SQL file at `sql/schema.sql` to create tables and policies.

## Tests
Run:
```bash
pytest
```

## Deployable Artifacts Checklist
- `app/` FastAPI app and services
- `requirements.txt`
- `sql/schema.sql`
- `.env.example`
- Render start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

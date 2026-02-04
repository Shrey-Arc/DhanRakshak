-- Users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY,
  email text,
  full_name text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS filings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) NOT NULL,
  status text NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filing_id uuid REFERENCES filings(id) NOT NULL,
  user_id uuid REFERENCES users(id) NOT NULL,
  document_type text NOT NULL,
  storage_path text NOT NULL,
  content_type text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ml_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filing_id uuid REFERENCES filings(id) NOT NULL,
  user_id uuid REFERENCES users(id) NOT NULL,
  parsed_json jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS risk_flags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filing_id uuid REFERENCES filings(id) UNIQUE NOT NULL,
  user_id uuid REFERENCES users(id) NOT NULL,
  flags jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS blockchain_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filing_id uuid REFERENCES filings(id) NOT NULL,
  user_id uuid REFERENCES users(id) NOT NULL,
  tx_hash text NOT NULL,
  payload_hash text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES users(id) NOT NULL,
  event_type text NOT NULL,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

-- RLS policies
ALTER TABLE filings ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ml_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE blockchain_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY select_own_filings ON filings
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_filings ON filings
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_filings ON filings
  FOR UPDATE USING (auth.uid() = user_id);

-- documents policy example
CREATE POLICY select_own_documents ON documents
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_documents ON documents
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_documents ON documents
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY delete_own_documents ON documents
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY select_own_ml_results ON ml_results
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_ml_results ON ml_results
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY select_own_risk_flags ON risk_flags
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_risk_flags ON risk_flags
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_risk_flags ON risk_flags
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY select_own_blockchain_records ON blockchain_records
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_blockchain_records ON blockchain_records
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY select_own_audit_logs ON audit_logs
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insert_own_audit_logs ON audit_logs
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Optional grants
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;

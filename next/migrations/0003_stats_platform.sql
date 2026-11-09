-- Migration number: 0003
-- Goldglitch Stats platform: users, memberships, payments (Wompi), sports data published by SQPC.
-- Legacy EGG store tables (orders) are left untouched; drop them manually once archived.
-- All timestamps are INTEGER epoch milliseconds (UTC).

CREATE TABLE IF NOT EXISTS users (
  id            TEXT PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE,
  display_name  TEXT,
  is_admin      INTEGER NOT NULL DEFAULT 0,
  created_at    INTEGER NOT NULL,
  last_login_at INTEGER
);

-- Magic-link tokens: only the SHA-256 of the token is stored.
CREATE TABLE IF NOT EXISTS login_tokens (
  token_hash TEXT PRIMARY KEY,
  email      TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  used_at    INTEGER
);
CREATE INDEX IF NOT EXISTS idx_login_tokens_email_created ON login_tokens(email, created_at);

-- Sessions: cookie carries the raw id, DB stores SHA-256.
CREATE TABLE IF NOT EXISTS sessions (
  id_hash    TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  user_agent TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- One membership row per user. Prepaid periods: each approved payment extends current_period_end.
CREATE TABLE IF NOT EXISTS subscriptions (
  user_id            TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  plan               TEXT NOT NULL CHECK (plan IN ('pro','elite')),
  current_period_end INTEGER NOT NULL,
  provider           TEXT NOT NULL,
  updated_at         INTEGER NOT NULL
);

-- id doubles as the payment reference sent to the provider.
CREATE TABLE IF NOT EXISTS payments (
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL REFERENCES users(id),
  plan            TEXT NOT NULL CHECK (plan IN ('pro','elite')),
  period          TEXT NOT NULL CHECK (period IN ('monthly','annual')),
  amount_in_cents INTEGER NOT NULL,
  currency        TEXT NOT NULL,
  provider        TEXT NOT NULL,
  provider_tx_id  TEXT UNIQUE,
  status          TEXT NOT NULL DEFAULT 'PENDING'
                  CHECK (status IN ('PENDING','APPROVED','DECLINED','VOIDED','ERROR')),
  applied_at      INTEGER,          -- set once the period extension was applied (idempotency)
  created_at      INTEGER NOT NULL,
  updated_at      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, created_at);

CREATE TABLE IF NOT EXISTS competitions (
  id      TEXT PRIMARY KEY,
  sport   TEXT NOT NULL CHECK (sport IN ('football','baseball')),
  name    TEXT NOT NULL,
  country TEXT,
  season  TEXT
);

CREATE TABLE IF NOT EXISTS teams (
  id         TEXT PRIMARY KEY,
  sport      TEXT NOT NULL CHECK (sport IN ('football','baseball')),
  name       TEXT NOT NULL,
  short_name TEXT,
  country    TEXT
);

CREATE TABLE IF NOT EXISTS matches (
  id             TEXT PRIMARY KEY,
  sport          TEXT NOT NULL CHECK (sport IN ('football','baseball')),
  competition_id TEXT NOT NULL REFERENCES competitions(id),
  home_team_id   TEXT NOT NULL REFERENCES teams(id),
  away_team_id   TEXT NOT NULL REFERENCES teams(id),
  kickoff_at     INTEGER NOT NULL,
  status         TEXT NOT NULL DEFAULT 'scheduled'
                 CHECK (status IN ('scheduled','live','finished','postponed','canceled')),
  home_score     INTEGER,
  away_score     INTEGER,
  venue          TEXT,
  updated_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_matches_kickoff ON matches(kickoff_at);
CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition_id, kickoff_at);

-- Latest model output per match and model version. Hot fields are columns; the rest lives in payload (JSON).
CREATE TABLE IF NOT EXISTS predictions (
  match_id      TEXT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  model_version TEXT NOT NULL,
  generated_at  INTEGER NOT NULL,
  p_home        REAL NOT NULL,
  p_draw        REAL,
  p_away        REAL NOT NULL,
  payload       TEXT NOT NULL,
  PRIMARY KEY (match_id, model_version)
);
CREATE INDEX IF NOT EXISTS idx_predictions_generated ON predictions(match_id, generated_at);

-- Public track record: out-of-sample scoring of past predictions.
CREATE TABLE IF NOT EXISTS model_metrics (
  id             TEXT PRIMARY KEY,
  sport          TEXT NOT NULL,
  competition_id TEXT,
  model_version  TEXT NOT NULL,
  window_start   INTEGER NOT NULL,
  window_end     INTEGER NOT NULL,
  n              INTEGER NOT NULL,
  brier          REAL NOT NULL,
  log_loss       REAL NOT NULL,
  baseline_brier REAL,
  calibration    TEXT NOT NULL,   -- JSON: [{bin, predicted, observed, n}]
  generated_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_model_metrics_sport ON model_metrics(sport, generated_at);

CREATE TABLE IF NOT EXISTS ingest_batches (
  id          TEXT PRIMARY KEY,   -- client batch id (idempotency key)
  received_at INTEGER NOT NULL,
  source      TEXT NOT NULL,
  records     INTEGER NOT NULL,
  body_sha256 TEXT NOT NULL
);

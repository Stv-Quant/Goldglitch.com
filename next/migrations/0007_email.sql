-- Password recovery tokens (only the SHA-256 is stored) and a log of every transactional email.
CREATE TABLE IF NOT EXISTS password_resets (
  token_hash TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  used_at    INTEGER
);
CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, created_at);

CREATE TABLE IF NOT EXISTS email_log (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     TEXT,
  email       TEXT NOT NULL,
  kind        TEXT NOT NULL,      -- magic_link | welcome | password_reset | password_changed | renewal_7d | renewal_1d | expired | payment_approved | test
  dedupe_key  TEXT UNIQUE,        -- set for emails that must go out at most once (welcome, reminders)
  status      TEXT NOT NULL CHECK (status IN ('sent','failed','skipped')),
  provider_id TEXT,
  error       TEXT,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_email_log_created ON email_log(created_at);
CREATE INDEX IF NOT EXISTS idx_email_log_user ON email_log(user_id, created_at);

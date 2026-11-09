-- Migration number: 0004
-- Password login (alongside magic links), forced password change, account status, CRM notes, admin audit log.

ALTER TABLE users ADD COLUMN password_hash TEXT;
ALTER TABLE users ADD COLUMN must_change_password INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active';  -- 'active' | 'suspended'
ALTER TABLE users ADD COLUMN tags TEXT;                                -- comma-separated CRM tags

-- Rate limiting for password logins (key = email or ip).
CREATE TABLE IF NOT EXISTS auth_attempts (
  id  INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL,
  at  INTEGER NOT NULL,
  ok  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_auth_attempts_key_at ON auth_attempts(key, at);

CREATE TABLE IF NOT EXISTS crm_notes (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  author_id  TEXT NOT NULL REFERENCES users(id),
  body       TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_crm_notes_user ON crm_notes(user_id, created_at);

-- Every admin action is recorded here and shown in the admin panel.
CREATE TABLE IF NOT EXISTS admin_audit (
  id             TEXT PRIMARY KEY,
  admin_id       TEXT NOT NULL,
  action         TEXT NOT NULL,
  target_user_id TEXT,
  detail         TEXT,
  created_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit(created_at);

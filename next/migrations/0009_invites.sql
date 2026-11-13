-- Admin invitation links: capped number of sign-ups, a deadline and an optional gift plan.
CREATE TABLE IF NOT EXISTS invites (
  id          TEXT PRIMARY KEY,
  code        TEXT NOT NULL UNIQUE,
  label       TEXT NOT NULL,
  max_uses    INTEGER NOT NULL CHECK (max_uses >= 1),
  uses        INTEGER NOT NULL DEFAULT 0,
  expires_at  INTEGER NOT NULL,
  gift_plan   TEXT CHECK (gift_plan IN ('pro','elite')),
  gift_days   INTEGER,
  created_by  TEXT NOT NULL,
  created_at  INTEGER NOT NULL,
  revoked_at  INTEGER
);
CREATE TABLE IF NOT EXISTS invite_redemptions (
  invite_id   TEXT NOT NULL REFERENCES invites(id) ON DELETE CASCADE,
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  redeemed_at INTEGER NOT NULL,
  PRIMARY KEY (invite_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_invite_redemptions_user ON invite_redemptions(user_id);
-- The invite travels inside the magic-link token, so it works even if the email is opened on another device.
ALTER TABLE login_tokens ADD COLUMN invite_code TEXT;

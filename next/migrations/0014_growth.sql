-- Organic growth measurement: where visitors come from and which sources turn into accounts and payments.
-- One row per day × source × landing page; a visitor is counted once per 30 min browsing session.
CREATE TABLE IF NOT EXISTS traffic_daily (
  day     TEXT NOT NULL,             -- YYYY-MM-DD (Colombia)
  source  TEXT NOT NULL,             -- instagram, facebook, tiktok, google, directo, ref:<tag>…
  landing TEXT NOT NULL,             -- first path of the visit (/, /planes, /historial, /app…)
  visits  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, source, landing)
);

ALTER TABLE users ADD COLUMN signup_source TEXT;   -- first-touch source of the visitor who created the account
ALTER TABLE users ADD COLUMN signup_ref TEXT;      -- ?ref= tag of a specific post/link, when there was one

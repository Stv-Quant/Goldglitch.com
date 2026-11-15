-- Combinadas guardadas por usuarios Pro. Cada selección es un pick de 75%+ que SQPC sigue (tracked_picks):
-- su resultado se toma de ahí por (match_id, label).
CREATE TABLE IF NOT EXISTS slips (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name       TEXT,
  legs       TEXT NOT NULL,
  p          REAL NOT NULL,
  first_kickoff INTEGER NOT NULL,
  last_kickoff  INTEGER NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_slips_user ON slips(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tracked_picks_match_label ON tracked_picks(match_id, label);

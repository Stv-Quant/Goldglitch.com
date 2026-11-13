-- Public track record of the picks SQPC chose before kickoff (featured ≥80% and validated value bets).
-- Rows are written by /api/ingest: inserted only if picked before kickoff; once settled they never change.
CREATE TABLE IF NOT EXISTS tracked_picks (
  id               TEXT PRIMARY KEY,
  kind             TEXT NOT NULL CHECK (kind IN ('featured','value')),
  sport            TEXT NOT NULL,
  competition_id   TEXT NOT NULL,
  competition_name TEXT,
  match_id         TEXT NOT NULL,
  home             TEXT NOT NULL,
  away             TEXT NOT NULL,
  kickoff_at       INTEGER NOT NULL,
  group_name       TEXT,
  label            TEXT NOT NULL,
  p                REAL NOT NULL,
  lo               REAL,
  hi               REAL,
  price            REAL,
  ev               REAL,
  status           TEXT NOT NULL CHECK (status IN ('pending','won','lost','void')),
  result           TEXT,
  picked_at        INTEGER NOT NULL,
  settled_at       INTEGER,
  profit           REAL,
  updated_at       INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tracked_picks_kickoff ON tracked_picks(kickoff_at);
CREATE INDEX IF NOT EXISTS idx_tracked_picks_status ON tracked_picks(status, kind, kickoff_at);

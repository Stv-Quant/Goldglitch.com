-- Allow basketball and hockey (SQPC publishes NBA, NCAA and NHL). SQLite cannot alter a CHECK, so the
-- sports tables are rebuilt: copy rows to plain backups, drop child-first, recreate, restore parent-first.
CREATE TABLE bk_competitions AS SELECT * FROM competitions;
CREATE TABLE bk_teams AS SELECT * FROM teams;
CREATE TABLE bk_matches AS SELECT * FROM matches;
CREATE TABLE bk_predictions AS SELECT * FROM predictions;

DROP TABLE predictions;
DROP TABLE matches;
DROP TABLE teams;
DROP TABLE competitions;

CREATE TABLE competitions (
  id      TEXT PRIMARY KEY,
  sport   TEXT NOT NULL CHECK (sport IN ('football','baseball','basketball','hockey')),
  name    TEXT NOT NULL,
  country TEXT,
  season  TEXT
);
CREATE TABLE teams (
  id         TEXT PRIMARY KEY,
  sport      TEXT NOT NULL CHECK (sport IN ('football','baseball','basketball','hockey')),
  name       TEXT NOT NULL,
  short_name TEXT,
  country    TEXT
);
CREATE TABLE matches (
  id             TEXT PRIMARY KEY,
  sport          TEXT NOT NULL CHECK (sport IN ('football','baseball','basketball','hockey')),
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
CREATE TABLE predictions (
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

INSERT INTO competitions (id, sport, name, country, season) SELECT id, sport, name, country, season FROM bk_competitions;
INSERT INTO teams (id, sport, name, short_name, country) SELECT id, sport, name, short_name, country FROM bk_teams;
INSERT INTO matches (id, sport, competition_id, home_team_id, away_team_id, kickoff_at, status, home_score, away_score, venue, updated_at)
  SELECT id, sport, competition_id, home_team_id, away_team_id, kickoff_at, status, home_score, away_score, venue, updated_at FROM bk_matches;
INSERT INTO predictions (match_id, model_version, generated_at, p_home, p_draw, p_away, payload)
  SELECT match_id, model_version, generated_at, p_home, p_draw, p_away, payload FROM bk_predictions;

DROP TABLE bk_predictions;
DROP TABLE bk_matches;
DROP TABLE bk_teams;
DROP TABLE bk_competitions;

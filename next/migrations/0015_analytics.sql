-- Full-funnel analytics without third parties or personal data: country, device, pages, engagement and heatmaps.
-- Sessions (one per 30 min) by day × country × source × device, and how many saw only one page (bounce).
CREATE TABLE IF NOT EXISTS visits_geo_daily (
  day         TEXT NOT NULL,              -- YYYY-MM-DD (Colombia)
  country     TEXT NOT NULL,              -- ISO-3166 alpha-2 from Cloudflare (XX = unknown)
  source      TEXT NOT NULL,              -- same channel names as traffic_daily
  device      TEXT NOT NULL,              -- mobile | tablet | desktop
  visits      INTEGER NOT NULL DEFAULT 0,
  single_page INTEGER NOT NULL DEFAULT 0, -- sessions that never reached a second page
  PRIMARY KEY (day, country, source, device)
);
-- Page views with engaged (visible) time and scroll depth, by normalized path (ids collapsed to :id).
CREATE TABLE IF NOT EXISTS pageviews_daily (
  day        TEXT NOT NULL,
  path       TEXT NOT NULL,
  country    TEXT NOT NULL,
  device     TEXT NOT NULL,
  views      INTEGER NOT NULL DEFAULT 0,
  exits      INTEGER NOT NULL DEFAULT 0,  -- views whose engagement report arrived (left the page)
  engaged_ms INTEGER NOT NULL DEFAULT 0,
  scroll_sum INTEGER NOT NULL DEFAULT 0,  -- sum of max scroll % per reported view
  PRIMARY KEY (day, path, country, device)
);
-- Click heatmap: x in 2% columns of the page width, y in 40 px rows from the top of the document.
CREATE TABLE IF NOT EXISTS heat_clicks (
  day    TEXT NOT NULL,
  path   TEXT NOT NULL,
  device TEXT NOT NULL,
  gx     INTEGER NOT NULL,
  gy     INTEGER NOT NULL,
  n      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, path, device, gx, gy)
);
-- What was clicked (buttons/links by label or data-track), to rank calls to action.
CREATE TABLE IF NOT EXISTS heat_targets (
  day    TEXT NOT NULL,
  path   TEXT NOT NULL,
  target TEXT NOT NULL,
  n      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, path, target)
);
-- Scroll reach: how many views got to each 10% band of the page.
CREATE TABLE IF NOT EXISTS heat_scroll (
  day    TEXT NOT NULL,
  path   TEXT NOT NULL,
  device TEXT NOT NULL,
  depth  INTEGER NOT NULL,                -- 0..10 (×10 %)
  n      INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, path, device, depth)
);
ALTER TABLE users ADD COLUMN signup_country TEXT;
ALTER TABLE users ADD COLUMN signup_device TEXT;

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  homepage_url TEXT NOT NULL,
  feed_url TEXT,
  enabled INTEGER NOT NULL DEFAULT 0,
  last_checked_at TEXT
);

CREATE TABLE IF NOT EXISTS articles (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id),
  canonical_url TEXT NOT NULL UNIQUE,
  original_title TEXT NOT NULL,
  author TEXT,
  published_at TEXT,
  updated_at TEXT,
  language TEXT,
  excerpt TEXT,
  content_hash TEXT,
  fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'developing',
  importance_score INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_articles (
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  PRIMARY KEY (event_id, article_id)
);

CREATE TABLE IF NOT EXISTS summaries (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  language TEXT NOT NULL CHECK (language IN ('en', 'bn')),
  short_summary TEXT NOT NULL,
  why_it_matters TEXT,
  background TEXT,
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  model_version TEXT,
  UNIQUE(event_id, language)
);

CREATE TABLE IF NOT EXISTS facts (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  fact_text TEXT NOT NULL,
  fact_type TEXT NOT NULL,
  source_article_id INTEGER REFERENCES articles(id),
  confidence_note TEXT
);

INSERT OR IGNORE INTO sources (name, homepage_url, enabled) VALUES
  ('The Daily Star', 'https://www.thedailystar.net/', 0),
  ('Dhaka Tribune', 'https://www.dhakatribune.com/', 0),
  ('The Financial Express', 'https://thefinancialexpress.com.bd/', 0),
  ('New Age', 'https://www.newagebd.net/', 0);

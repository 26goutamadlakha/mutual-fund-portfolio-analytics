CREATE TABLE IF NOT EXISTS nav_history (
  date TEXT NOT NULL,
  scheme_code TEXT NOT NULL,
  fund_name TEXT NOT NULL,
  nav REAL NOT NULL CHECK (nav > 0),
  PRIMARY KEY (date, scheme_code)
);
CREATE TABLE IF NOT EXISTS benchmark_history (
  date TEXT NOT NULL,
  benchmark_name TEXT NOT NULL,
  close REAL NOT NULL CHECK (close > 0),
  PRIMARY KEY (date, benchmark_name)
);
CREATE TABLE IF NOT EXISTS fund_metadata (
  scheme_code TEXT PRIMARY KEY,
  fund_name TEXT NOT NULL,
  category TEXT,
  benchmark_name TEXT
);

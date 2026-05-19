"""
SQLite storage layer for the Ligat Ha'Al predictor.

Two tables:
  raw_matches       — one row per fixture (all statuses)
  calibration_table — one row per completed fixture with computed features

On first init, any existing raw_matches.csv / calibration_table.csv are
automatically migrated into the DB so the transition is seamless.
"""
import csv as csv_mod
import io
import os
import sqlite3

import config

MATCH_COLS = [
    "fixture_id", "season", "date", "round", "status",
    "home_team", "home_team_id", "away_team", "away_team_id",
    "home_goals", "away_goals",
]

CALIB_COLS = [
    "fixture_id", "season", "date", "home_team", "away_team",
    "home_ppg", "away_ppg", "ppg_diff",
    "home_matches_played", "away_matches_played",
    "home_form", "away_form", "form_diff",
    "h2h_diff", "h2h_matches", "result",
]

_CREATE = """
CREATE TABLE IF NOT EXISTS raw_matches (
    fixture_id   TEXT PRIMARY KEY,
    season       INTEGER,
    date         TEXT,
    round        TEXT,
    status       TEXT,
    home_team    TEXT,
    home_team_id TEXT,
    away_team    TEXT,
    away_team_id TEXT,
    home_goals   INTEGER,
    away_goals   INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_match_key
    ON raw_matches(substr(date, 1, 10), home_team, away_team);

CREATE TABLE IF NOT EXISTS calibration_table (
    fixture_id          TEXT PRIMARY KEY,
    season              INTEGER,
    date                TEXT,
    home_team           TEXT,
    away_team           TEXT,
    home_ppg            REAL,
    away_ppg            REAL,
    ppg_diff            REAL,
    home_matches_played INTEGER,
    away_matches_played INTEGER,
    home_form           REAL,
    away_form           REAL,
    form_diff           REAL,
    h2h_diff            REAL,
    h2h_matches         INTEGER,
    result              TEXT
);
"""


def get_conn():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(_CREATE)
        _migrate_csv_if_needed(conn)


# ── type helpers ──────────────────────────────────────────────────────────────

def _goal(v):
    if v in (None, "", "None"):
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _real(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _int(v):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


# ── raw_matches ───────────────────────────────────────────────────────────────

def _match_params(r):
    return (
        r.get("fixture_id"),
        _int(r.get("season")),
        r.get("date"),
        r.get("round"),
        r.get("status"),
        r.get("home_team"),
        r.get("home_team_id", ""),
        r.get("away_team"),
        r.get("away_team_id", ""),
        _goal(r.get("home_goals")),
        _goal(r.get("away_goals")),
    )


def _raw_insert(conn, rows):
    # Update mutable fields on existing fixture_ids (e.g. NS → FT).
    conn.executemany(
        "UPDATE raw_matches SET status=?, home_goals=?, away_goals=?, round=? "
        "WHERE fixture_id=?",
        [(r.get("status"), _goal(r.get("home_goals")), _goal(r.get("away_goals")),
          r.get("round"), r.get("fixture_id")) for r in rows],
    )
    # Insert genuinely new matches; unique index on (date[:10], home, away) blocks
    # cross-source duplicates silently.
    conn.executemany(
        f"INSERT OR IGNORE INTO raw_matches ({', '.join(MATCH_COLS)}) "
        f"VALUES ({', '.join('?' * len(MATCH_COLS))})",
        [_match_params(r) for r in rows],
    )


def insert_matches(rows):
    """Upsert rows into raw_matches. Returns (added, updated_or_skipped)."""
    with get_conn() as conn:
        before = conn.execute("SELECT COUNT(*) FROM raw_matches").fetchone()[0]
        _raw_insert(conn, rows)
        after = conn.execute("SELECT COUNT(*) FROM raw_matches").fetchone()[0]
    added = after - before
    return added, len(rows) - added


def fetch_all_matches():
    """Return all raw_matches as list of dicts, chronologically sorted."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM raw_matches ORDER BY date, fixture_id"
        ).fetchall()
    return [dict(r) for r in rows]


# ── calibration_table ─────────────────────────────────────────────────────────

def _calib_params(r):
    return (
        r.get("fixture_id"),
        _int(r.get("season")),
        r.get("date"),
        r.get("home_team"),
        r.get("away_team"),
        _real(r.get("home_ppg")),
        _real(r.get("away_ppg")),
        _real(r.get("ppg_diff")),
        _int(r.get("home_matches_played")),
        _int(r.get("away_matches_played")),
        _real(r.get("home_form")),
        _real(r.get("away_form")),
        _real(r.get("form_diff")),
        _real(r.get("h2h_diff")),
        _int(r.get("h2h_matches")),
        r.get("result"),
    )


def replace_calibration(rows):
    """Wipe and rebuild the calibration table."""
    with get_conn() as conn:
        conn.execute("DELETE FROM calibration_table")
        conn.executemany(
            f"INSERT INTO calibration_table ({', '.join(CALIB_COLS)}) "
            f"VALUES ({', '.join('?' * len(CALIB_COLS))})",
            [_calib_params(r) for r in rows],
        )


def fetch_calibration():
    """Return all calibration rows as list of dicts."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM calibration_table ORDER BY date, fixture_id"
        ).fetchall()
    return [dict(r) for r in rows]


# ── CSV export ────────────────────────────────────────────────────────────────

def export_matches_csv():
    buf = io.StringIO()
    writer = csv_mod.DictWriter(buf, fieldnames=MATCH_COLS)
    writer.writeheader()
    writer.writerows(fetch_all_matches())
    return buf.getvalue()


def export_calibration_csv():
    buf = io.StringIO()
    writer = csv_mod.DictWriter(buf, fieldnames=CALIB_COLS)
    writer.writeheader()
    writer.writerows(fetch_calibration())
    return buf.getvalue()


# ── one-time CSV migration ────────────────────────────────────────────────────

def _migrate_csv_if_needed(conn):
    if conn.execute("SELECT COUNT(*) FROM raw_matches").fetchone()[0] > 0:
        return

    raw_csv = os.path.join(config.DATA_DIR, "raw_matches.csv")
    try:
        with open(raw_csv, encoding="utf-8") as f:
            rows = list(csv_mod.DictReader(f))
        _raw_insert(conn, rows)
        print(f"[db] Migrated {len(rows)} rows from raw_matches.csv")
    except FileNotFoundError:
        pass

    calib_csv = os.path.join(config.DATA_DIR, "calibration_table.csv")
    try:
        with open(calib_csv, encoding="utf-8") as f:
            rows = list(csv_mod.DictReader(f))
        conn.executemany(
            f"INSERT OR REPLACE INTO calibration_table ({', '.join(CALIB_COLS)}) "
            f"VALUES ({', '.join('?' * len(CALIB_COLS))})",
            [_calib_params(r) for r in rows],
        )
        print(f"[db] Migrated {len(rows)} rows from calibration_table.csv")
    except FileNotFoundError:
        pass

"""
Alternative data source: TheSportsDB (free, no key needed).
Use this to pull seasons that API-Football's free tier doesn't cover (e.g. 2025/26).

TheSportsDB returns matches round-by-round. We pull until a round comes back empty.
Results are upserted into the SQLite database (duplicates skipped by date+teams key).
After running this, re-run build_features.py and calibrate.py.

Usage:
    python pull_thesportsdb.py               # pulls season 2025
    python pull_thesportsdb.py 2025          # pulls season 2025/26
"""
import json
import sys
import time
import urllib.error
import urllib.request

import config
import db

LEAGUE_ID   = 4644
BASE_URL    = "https://www.thesportsdb.com/api/v1/json/123"
MAX_ROUNDS  = 50

NAME_MAP = {
    "FC Ashdod":                  "Ashdod",
    "Hapoel Be'er Sheva":         "Hapoel Beer Sheva",
    "Hapoel Ironi Kiryat Shmona": "Ironi Kiryat Shmona",
    "Hapoel Tel-Aviv":            "Hapoel Tel Aviv",
}

FINISHED_STATUSES = {"Match Finished", "FT", "AET", "PEN"}


def _get(path):
    url = f"{BASE_URL}/{path}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 30 * (attempt + 1)
                print(f"  Rate limited — waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                sys.exit(f"HTTP error {e.code}: {e.read().decode()[:200]}")
        except urllib.error.URLError as e:
            sys.exit(f"Network error: {e.reason}")
    sys.exit("Rate limit not cleared after retries. Wait a few minutes and try again.")


def _norm(name):
    return NAME_MAP.get(name, name)


def pull_season(season_year):
    season_str = f"{season_year}-{season_year + 1}"
    print(f"Pulling Ligat Ha'Al {season_str} from TheSportsDB...")

    rows = []
    for round_num in range(1, MAX_ROUNDS + 1):
        data = _get(f"eventsround.php?id={LEAGUE_ID}&r={round_num}&s={season_str}")
        events = data.get("events") or []
        if not events:
            print(f"  Round {round_num}: empty — done ({round_num - 1} rounds pulled)")
            break

        for e in events:
            status = "FT" if e.get("strStatus") in FINISHED_STATUSES else "NS"
            hg = e.get("intHomeScore")
            ag = e.get("intAwayScore")
            rows.append({
                "fixture_id":   f"sdb_{e['idEvent']}",
                "season":       season_year,
                "date":         (e.get("strTimestamp") or e.get("dateEvent") or ""),
                "round":        f"Regular Season - {e.get('intRound', round_num)}",
                "status":       status,
                "home_team":    _norm(e["strHomeTeam"]),
                "home_team_id": e.get("idHomeTeam", ""),
                "away_team":    _norm(e["strAwayTeam"]),
                "away_team_id": e.get("idAwayTeam", ""),
                "home_goals":   int(hg) if hg is not None else None,
                "away_goals":   int(ag) if ag is not None else None,
            })
        print(f"  Round {round_num}: {len(events)} events")
        time.sleep(2.5)

    return rows


if __name__ == "__main__":
    db.init_db()
    season_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    rows = pull_season(season_year)
    if not rows:
        print("No data returned.")
        sys.exit(0)

    added, skipped = db.insert_matches(rows)
    completed = sum(1 for r in rows if r["status"] == "FT")
    print(f"\nAdded {added} new rows ({skipped} already existed).")
    print(f"{completed} of {len(rows)} pulled matches are completed.")
    if added:
        print("\nNext steps:")
        print("  python build_features.py")
        print("  python calibrate.py")

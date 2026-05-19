"""
Step 1 of the pipeline: pull historical fixtures for the Israeli Premier League
from API-Football and save them to a local CSV.

You run this rarely: once to grab history, then once a week to add new results.
The prediction model itself never touches the API — it works off the saved CSV.

Usage:
    export APIFOOTBALL_KEY="your_key"
    python pull_data.py
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import config


def _api_get(path, params):
    """Make a single GET request to API-Football and return the parsed body."""
    if not config.API_KEY:
        sys.exit('No API key. Run:  export APIFOOTBALL_KEY="your_key"  then try again.')
    url = f"{config.API_BASE}/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"x-apisports-key": config.API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP error {e.code} calling /{path}: {e.read().decode()[:200]}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error calling /{path}: {e.reason}")
    # API-Football reports problems inside the body, not via HTTP status codes.
    if body.get("errors"):
        sys.exit(f"API returned errors for /{path}: {body['errors']}")
    return body


def discover_league_id():
    """Look up candidate league ids for Israel and print them for you to choose."""
    print("LEAGUE_ID is not set. Looking up Israeli leagues...\n")
    body = _api_get("leagues", {"country": "Israel"})
    for item in body.get("response", []):
        league = item.get("league", {})
        country = item.get("country", {})
        print(f"  id={league.get('id'):<6} {league.get('name')}  "
              f"({country.get('name')}, {league.get('type')})")
    print("\nPick the Israeli Premier League id above, set LEAGUE_ID in "
          "config.py, then run this again.")


def pull_fixtures():
    """Pull every fixture for each configured season and write raw_matches.csv."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    rows = []
    for season in config.SEASONS:
        print(f"Pulling season {season}/{season + 1}...")
        body = _api_get("fixtures", {"league": config.LEAGUE_ID, "season": season})
        season_rows = body.get("response", [])
        for item in season_rows:
            fx = item.get("fixture", {})
            lg = item.get("league", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            rows.append({
                "fixture_id": fx.get("id"),
                "season": season,
                "date": fx.get("date"),
                "round": lg.get("round"),
                "status": (fx.get("status") or {}).get("short"),
                "home_team": (teams.get("home") or {}).get("name"),
                "home_team_id": (teams.get("home") or {}).get("id"),
                "away_team": (teams.get("away") or {}).get("name"),
                "away_team_id": (teams.get("away") or {}).get("id"),
                "home_goals": goals.get("home"),
                "away_goals": goals.get("away"),
            })
        print(f"  got {len(season_rows)} fixtures")
        time.sleep(1)  # be polite to the free tier

    rows.sort(key=lambda r: (r["date"] or "", r["fixture_id"] or 0))
    fieldnames = ["fixture_id", "season", "date", "round", "status",
                  "home_team", "home_team_id", "away_team", "away_team_id",
                  "home_goals", "away_goals"]
    with open(config.RAW_MATCHES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    completed = sum(1 for r in rows if r["status"] == "FT")
    print(f"\nWrote {len(rows)} fixtures ({completed} completed) to {config.RAW_MATCHES}")


if __name__ == "__main__":
    if config.LEAGUE_ID is None:
        discover_league_id()
    else:
        pull_fixtures()

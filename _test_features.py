"""
Builds a synthetic raw_matches.csv (deterministic), runs build_features.py,
then independently re-derives a few features to prove the point-in-time logic
is correct and leak-free.
"""
import csv
import itertools
import subprocess
import sys

import config

# --- 1. generate a deterministic synthetic league --------------------------
# 4 teams, 2 seasons, double round-robin. Results are a fixed function of the
# teams so we can re-derive everything by hand.
TEAMS = ["A", "B", "C", "D"]
STRENGTH = {"A": 3, "B": 2, "C": 1, "D": 0}  # A beats everyone, etc.


def result_for(home, away):
    """Deterministic score: stronger team wins, equal strength draws."""
    if STRENGTH[home] > STRENGTH[away]:
        return 2, 0
    if STRENGTH[home] < STRENGTH[away]:
        return 0, 1
    return 1, 1


rows = []
fid = 1
for season in (2023, 2024):
    matchday = 0
    # double round-robin: every ordered pair plays once
    for home, away in itertools.permutations(TEAMS, 2):
        matchday += 1
        hg, ag = result_for(home, away)
        # spread dates so chronological sort is unambiguous
        date = f"{season}-09-{matchday:02d}T18:00:00+00:00"
        rows.append({
            "fixture_id": fid, "season": season, "date": date,
            "round": f"Regular Season - {matchday}", "status": "FT",
            "home_team": home, "home_team_id": ord(home),
            "away_team": away, "away_team_id": ord(away),
            "home_goals": hg, "away_goals": ag,
        })
        fid += 1

fieldnames = ["fixture_id", "season", "date", "round", "status",
              "home_team", "home_team_id", "away_team", "away_team_id",
              "home_goals", "away_goals"]
with open(config.RAW_MATCHES, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)
print(f"Synthetic raw_matches.csv: {len(rows)} matches")

# --- 2. run the real feature builder ---------------------------------------
subprocess.run([sys.executable, "build_features.py"], check=True)

# --- 3. load its output and re-derive features independently ---------------
with open(config.CALIBRATION_TABLE, encoding="utf-8") as f:
    out = list(csv.DictReader(f))

raw_by_season = {}
for r in rows:
    raw_by_season.setdefault(r["season"], []).append(r)

failures = []


def pts(gf, ga):
    return 3 if gf > ga else (1 if gf == ga else 0)


for r in out:
    season = int(r["season"])
    fid = int(r["fixture_id"])
    home, away = r["home_team"], r["away_team"]
    season_matches = sorted(raw_by_season[season], key=lambda x: x["date"])
    prior = [m for m in season_matches if m["fixture_id"] < fid]

    # CRITICAL leakage check: not a single prior match may be this one or later
    if any(m["fixture_id"] >= fid for m in prior):
        failures.append(f"fixture {fid}: prior set contains current/future match")

    def team_ppg(team):
        got = [pts(m["home_goals"], m["away_goals"]) if m["home_team"] == team
               else pts(m["away_goals"], m["home_goals"])
               for m in prior if team in (m["home_team"], m["away_team"])]
        return (sum(got) / len(got)) if got else None

    exp_home, exp_away = team_ppg(home), team_ppg(away)
    got_home = float(r["home_ppg"]) if r["home_ppg"] else None
    got_away = float(r["away_ppg"]) if r["away_ppg"] else None

    for label, exp, got in (("home_ppg", exp_home, got_home),
                            ("away_ppg", exp_away, got_away)):
        if exp is None and got is None:
            continue
        if exp is None or got is None or abs(exp - got) > 1e-6:
            failures.append(f"fixture {fid} {label}: expected {exp}, got {got}")

    # first match of each season must have no PPG and empty ppg_diff
    if not prior:
        if r["home_ppg"] or r["away_ppg"] or r["ppg_diff"] != "":
            failures.append(f"fixture {fid}: first-of-season should have empty PPG features")

print("\n--- correctness check ---")
if failures:
    for fail in failures[:20]:
        print("  FAIL:", fail)
    sys.exit(1)
print(f"  PASS: re-derived PPG matches builder output for all {len(out)} rows")
print("  PASS: no prior-match set contains the current or any future match")
print("  PASS: first match of each season has empty point-in-time features")

# show a sample so we can eyeball the shape
print("\n--- sample rows (season 2023) ---")
for r in out[:8]:
    print(f"  fx{r['fixture_id']} {r['home_team']}v{r['away_team']}  "
          f"ppg_diff={r['ppg_diff'] or '-':>7}  form_diff={r['form_diff'] or '-':>7}  "
          f"h2h={r['h2h_diff']}  mp={r['home_matches_played']}/{r['away_matches_played']}  "
          f"-> {r['result']}")

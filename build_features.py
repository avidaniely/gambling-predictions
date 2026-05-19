"""
Step 2 of the pipeline: turn raw_matches.csv into a calibration table.

For every completed match it reconstructs the "automatic" parameters *as they
stood the moment before kick-off* — never using the match itself or anything
later. That point-in-time discipline is the whole game: it is what stops the
model from looking brilliant in calibration and then failing in real life
(the data-leakage trap).

Parameters built here:
  - ppg_diff   : difference in points-per-game (current season, prior matches only)
  - form_diff  : difference in opponent-adjusted, exponentially-decayed recent form
  - h2h_diff   : difference in head-to-head points over a fresh window

Home advantage is deliberately NOT a column. It is not a comparison between the
teams — it is a constant bias toward the home side, so the regression captures
it as its intercept. Nothing to compute here.

Motivation and injuries are also not here: they have no historical record to
reconstruct. They join the model later as manually-entered inputs.

Usage:
    python build_features.py
"""
import csv
import sys
from collections import defaultdict, deque

import config

COMPLETED = {"FT", "AET", "PEN"}


def points(gf, ga):
    """Points earned by a team that scored gf against ga."""
    if gf > ga:
        return 3
    if gf == ga:
        return 1
    return 0


def load_completed_matches():
    """Load completed matches, chronologically sorted, with numeric goals."""
    try:
        with open(config.RAW_MATCHES, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        sys.exit(f"{config.RAW_MATCHES} not found — run pull_data.py first.")
    matches = []
    for r in rows:
        if r["status"] not in COMPLETED:
            continue
        if r["home_goals"] in ("", None) or r["away_goals"] in ("", None):
            continue
        r["home_goals"] = int(r["home_goals"])
        r["away_goals"] = int(r["away_goals"])
        r["season"] = int(r["season"])
        matches.append(r)
    matches.sort(key=lambda r: (r["date"], str(r["fixture_id"])))
    return matches


def build():
    matches = load_completed_matches()
    if not matches:
        sys.exit("No completed matches found in raw_matches.csv.")

    # Running history of PRIOR matches only. Keyed by season so PPG and form do
    # not bleed across season boundaries. H2H is keyed by team pair, across seasons.
    season_team_points = defaultdict(lambda: defaultdict(list))   # season -> team -> [pts,...]
    season_team_form = defaultdict(lambda: defaultdict(deque))    # season -> team -> deque[(pts, opp_ppg)]
    h2h_history = defaultdict(list)                              # (teamA,teamB) -> [(season,home,pts_h,pts_a),...]

    def ppg_now(season, team):
        pts = season_team_points[season][team]
        if not pts:
            return None, 0
        return sum(pts) / len(pts), len(pts)

    def league_avg_ppg(season):
        all_pts = [p for team in season_team_points[season].values() for p in team]
        if len(all_pts) < 10:  # too early in the season to trust
            return config.LEAGUE_AVG_PPG_FALLBACK
        return sum(all_pts) / len(all_pts)

    def form_now(season, team):
        """Opponent-adjusted, exponentially-decayed form over the last N matches."""
        window = season_team_form[season][team]
        if not window:
            return None
        avg_ppg = league_avg_ppg(season)
        weighted_sum, weight_total = 0.0, 0.0
        for i, (pts, opp_ppg) in enumerate(reversed(window)):  # i=0 is most recent
            w = config.FORM_DECAY ** i
            opp_factor = (opp_ppg / avg_ppg) if (opp_ppg and avg_ppg) else 1.0
            weighted_sum += w * pts * opp_factor
            weight_total += w
        return weighted_sum / weight_total if weight_total else None

    def h2h_diff_now(home, away, season):
        key = tuple(sorted([home, away]))
        cutoff = season - config.H2H_SEASONS_BACK
        relevant = [m for m in h2h_history[key] if m[0] >= cutoff]
        if not relevant:
            return 0.0, 0
        home_pts = [m[2] if m[1] == home else m[3] for m in relevant]
        away_pts = [m[3] if m[1] == home else m[2] for m in relevant]
        diff = sum(home_pts) / len(home_pts) - sum(away_pts) / len(away_pts)
        return diff, len(relevant)

    def diff(a, b):
        return "" if (a is None or b is None) else round(a - b, 4)

    out_rows = []
    for m in matches:
        season, home, away = m["season"], m["home_team"], m["away_team"]
        hg, ag = m["home_goals"], m["away_goals"]

        # ---- features from history BEFORE this match ----------------------
        home_ppg, home_mp = ppg_now(season, home)
        away_ppg, away_mp = ppg_now(season, away)
        home_form = form_now(season, home)
        away_form = form_now(season, away)
        h2h_diff, h2h_n = h2h_diff_now(home, away, season)

        result = "H" if hg > ag else ("D" if hg == ag else "A")

        out_rows.append({
            "fixture_id": m["fixture_id"],
            "season": season,
            "date": m["date"],
            "home_team": home,
            "away_team": away,
            "home_ppg": round(home_ppg, 4) if home_ppg is not None else "",
            "away_ppg": round(away_ppg, 4) if away_ppg is not None else "",
            "ppg_diff": diff(home_ppg, away_ppg),
            "home_matches_played": home_mp,
            "away_matches_played": away_mp,
            "home_form": round(home_form, 4) if home_form is not None else "",
            "away_form": round(away_form, 4) if away_form is not None else "",
            "form_diff": diff(home_form, away_form),
            "h2h_diff": round(h2h_diff, 4),
            "h2h_matches": h2h_n,
            "result": result,
        })

        # ---- ONLY NOW record this match into history ----------------------
        hp, ap = points(hg, ag), points(ag, hg)
        # opponent PPG "as of now", stored so future form calcs can adjust by it
        home_ppg_at_time = home_ppg if home_ppg is not None else config.LEAGUE_AVG_PPG_FALLBACK
        away_ppg_at_time = away_ppg if away_ppg is not None else config.LEAGUE_AVG_PPG_FALLBACK

        season_team_points[season][home].append(hp)
        season_team_points[season][away].append(ap)

        season_team_form[season][home].append((hp, away_ppg_at_time))
        season_team_form[season][away].append((ap, home_ppg_at_time))
        while len(season_team_form[season][home]) > config.FORM_WINDOW:
            season_team_form[season][home].popleft()
        while len(season_team_form[season][away]) > config.FORM_WINDOW:
            season_team_form[season][away].popleft()

        h2h_history[tuple(sorted([home, away]))].append((season, home, hp, ap))

    fieldnames = ["fixture_id", "season", "date", "home_team", "away_team",
                  "home_ppg", "away_ppg", "ppg_diff",
                  "home_matches_played", "away_matches_played",
                  "home_form", "away_form", "form_diff",
                  "h2h_diff", "h2h_matches", "result"]
    with open(config.CALIBRATION_TABLE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    reliable = sum(1 for r in out_rows
                   if r["home_matches_played"] >= config.MIN_MATCHES_FOR_PPG
                   and r["away_matches_played"] >= config.MIN_MATCHES_FOR_PPG)
    print(f"Wrote {len(out_rows)} matches to {config.CALIBRATION_TABLE}")
    print(f"  {reliable} have a reliable PPG for both teams "
          f"(>= {config.MIN_MATCHES_FOR_PPG} prior matches each)")
    print(f"  {len(out_rows) - reliable} are early-season rows — "
          f"keep or filter them at calibration time")


if __name__ == "__main__":
    build()

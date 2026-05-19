"""
Stage 4: local web portal for Ligat Ha'Al match predictions.

Reads from the SQLite database — never touches the API directly.
Run pull_data.py, build_features.py, and calibrate.py first.

Usage:
    python app.py
    open http://localhost:5000
"""
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import defaultdict, deque

try:
    from flask import Flask, Response, render_template, request
except ImportError:
    sys.exit("app.py needs Flask.  Install:  pip install flask")

import config
import db

app = Flask(__name__)
db.init_db()  # create tables + migrate CSVs on first run

COMPLETED = {"FT", "AET", "PEN"}

STAKE_OPTIONS = [
    (10, "Title race / Relegation survival"),
    (7,  "European qualification"),
    (6,  "Playoff spot"),
    (5,  "Mid-table (no clear objective)"),
    (2,  "Nothing at stake"),
]
DERBY_BONUS   = 2
RIVALRY_BONUS = 1


# ── data helpers ──────────────────────────────────────────────────────────────

def _pts(gf, ga):
    return 3 if gf > ga else (1 if gf == ga else 0)


def load_matches():
    rows = db.fetch_all_matches()
    for r in rows:
        r["season"] = int(r["season"])
        if r["home_goals"] is not None and r["away_goals"] is not None:
            r["home_goals"] = int(r["home_goals"])
            r["away_goals"] = int(r["away_goals"])
    return rows


def load_model():
    try:
        with open(config.MODEL_WEIGHTS, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def build_state(matches):
    s_pts   = defaultdict(lambda: defaultdict(list))
    s_form  = defaultdict(lambda: defaultdict(deque))
    s_wdl   = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    s_gf    = defaultdict(lambda: defaultdict(int))
    s_ga    = defaultdict(lambda: defaultdict(int))
    s_last5 = defaultdict(lambda: defaultdict(list))
    h2h     = defaultdict(list)

    def league_avg(season):
        all_pts = [p for pts in s_pts[season].values() for p in pts]
        return sum(all_pts) / len(all_pts) if len(all_pts) >= 10 else config.LEAGUE_AVG_PPG_FALLBACK

    def _form(season, team):
        window = s_form[season][team]
        if not window:
            return None
        avg = league_avg(season)
        ws, wt = 0.0, 0.0
        for i, (pts, opp_ppg) in enumerate(reversed(window)):
            w = config.FORM_DECAY ** i
            opp_factor = (opp_ppg / avg) if (opp_ppg and avg) else 1.0
            ws += w * pts * opp_factor
            wt += w
        return ws / wt if wt else None

    all_teams_by_season = defaultdict(set)
    for m in matches:
        all_teams_by_season[m["season"]].add(m["home_team"])
        all_teams_by_season[m["season"]].add(m["away_team"])

    for m in matches:
        if m["status"] not in COMPLETED:
            continue
        season = m["season"]
        home, away = m["home_team"], m["away_team"]
        hg, ag = m["home_goals"], m["away_goals"]
        hp, ap = _pts(hg, ag), _pts(ag, hg)

        home_ppg_now = (sum(s_pts[season][home]) / len(s_pts[season][home])
                        if s_pts[season][home] else config.LEAGUE_AVG_PPG_FALLBACK)
        away_ppg_now = (sum(s_pts[season][away]) / len(s_pts[season][away])
                        if s_pts[season][away] else config.LEAGUE_AVG_PPG_FALLBACK)

        s_pts[season][home].append(hp)
        s_pts[season][away].append(ap)

        s_form[season][home].append((hp, away_ppg_now))
        s_form[season][away].append((ap, home_ppg_now))
        while len(s_form[season][home]) > config.FORM_WINDOW:
            s_form[season][home].popleft()
        while len(s_form[season][away]) > config.FORM_WINDOW:
            s_form[season][away].popleft()

        if hp == 3:
            s_wdl[season][home][0] += 1
        elif hp == 1:
            s_wdl[season][home][1] += 1
        else:
            s_wdl[season][home][2] += 1
        if ap == 3:
            s_wdl[season][away][0] += 1
        elif ap == 1:
            s_wdl[season][away][1] += 1
        else:
            s_wdl[season][away][2] += 1

        s_gf[season][home] += hg
        s_ga[season][home] += ag
        s_gf[season][away] += ag
        s_ga[season][away] += hg

        home_letter = "W" if hp == 3 else ("D" if hp == 1 else "L")
        away_letter = "W" if ap == 3 else ("D" if ap == 1 else "L")
        s_last5[season][home].append(home_letter)
        s_last5[season][away].append(away_letter)

        h2h[tuple(sorted([home, away]))].append((season, home, hp, ap))

    states = {}
    for season, teams in all_teams_by_season.items():
        states[season] = {}
        for team in teams:
            pts_list = s_pts[season][team]
            wdl = s_wdl[season][team]
            played = len(pts_list)
            states[season][team] = {
                "ppg":    sum(pts_list) / played if played else None,
                "form":   _form(season, team),
                "played": played,
                "wins":   wdl[0],
                "draws":  wdl[1],
                "losses": wdl[2],
                "points": sum(pts_list),
                "gf":     s_gf[season][team],
                "ga":     s_ga[season][team],
                "last5":  s_last5[season][team][-5:],
            }
    return states, h2h


def get_features(home, away, season, states, h2h_history):
    hs  = states.get(season, {}).get(home, {})
    aws = states.get(season, {}).get(away, {})

    home_ppg  = hs.get("ppg")
    away_ppg  = aws.get("ppg")
    home_form = hs.get("form")
    away_form = aws.get("form")

    key    = tuple(sorted([home, away]))
    cutoff = season - config.H2H_SEASONS_BACK
    rel    = [m for m in h2h_history[key] if m[0] >= cutoff]
    if rel:
        h_pts = [m[2] if m[1] == home else m[3] for m in rel]
        a_pts = [m[3] if m[1] == home else m[2] for m in rel]
        h2hd  = sum(h_pts) / len(h_pts) - sum(a_pts) / len(a_pts)
        h2h_n = len(rel)
    else:
        h2hd, h2h_n = 0.0, 0

    return {
        "ppg_diff":    (home_ppg - away_ppg)   if home_ppg  is not None and away_ppg  is not None else 0.0,
        "form_diff":   (home_form - away_form)  if home_form is not None and away_form is not None else 0.0,
        "h2h_diff":    h2hd,
        "home_ppg":    home_ppg,
        "away_ppg":    away_ppg,
        "home_form":   home_form,
        "away_form":   away_form,
        "home_played": hs.get("played", 0),
        "away_played": aws.get("played", 0),
        "h2h_n":       h2h_n,
    }


def predict_probs(features, mot_diff, inj_diff, model):
    coef      = model["coef"]
    intercept = model["intercept"]
    w_mot     = model["manual_weights"]["motivation_diff"]
    w_inj     = model["manual_weights"]["injury_diff"]

    raw = {}
    for cls in model["classes"]:
        raw[cls] = intercept[cls] + sum(
            coef[cls][f] * features.get(f, 0.0) for f in model["features"]
        )

    adj = w_mot * mot_diff + w_inj * inj_diff
    raw["H"] = raw.get("H", 0.0) + adj
    raw["A"] = raw.get("A", 0.0) - adj

    max_r = max(raw.values())
    exp_r = {c: math.exp(s - max_r) for c, s in raw.items()}
    total = sum(exp_r.values())
    return {c: exp_r[c] / total for c in raw}


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    matches = load_matches()
    if not matches:
        return "No data found. Run pull_data.py first.", 500

    latest_season = max(m["season"] for m in matches)
    states, _ = build_state(matches)

    team_states = states.get(latest_season, {})
    standings = sorted(
        [{"team": t, **s} for t, s in team_states.items() if s["played"] > 0],
        key=lambda r: (-r["points"], -(r["gf"] - r["ga"]), -r["gf"]),
    )
    teams = sorted(team_states.keys())

    return render_template(
        "index.html",
        active="home",
        season=latest_season,
        standings=standings,
        teams=teams,
    )


@app.route("/predict", methods=["GET", "POST"])
def predict():
    matches = load_matches()
    model   = load_model()

    if not matches:
        return "No data found. Run pull_data.py first.", 500
    if not model:
        return "No model found. Run calibrate.py first.", 500

    latest_season = max(m["season"] for m in matches)
    states, h2h_history = build_state(matches)
    teams = sorted(states.get(latest_season, {}).keys())

    form_vals = {
        "home": request.args.get("home", ""),
        "away": request.args.get("away", ""),
        "home_stake":   5,
        "away_stake":   5,
        "home_derby":   False,
        "away_derby":   False,
        "home_rivalry": False,
        "away_rivalry": False,
        "home_injury":  0,
        "away_injury":  0,
    }

    features   = None
    prediction = None
    mot_diff   = 0
    inj_diff   = 0

    if request.method == "POST":
        home = request.form.get("home", "").strip()
        away = request.form.get("away", "").strip()

        form_vals.update({
            "home":         home,
            "away":         away,
            "home_stake":   int(request.form.get("home_stake", 5)),
            "away_stake":   int(request.form.get("away_stake", 5)),
            "home_derby":   bool(request.form.get("home_derby")),
            "away_derby":   bool(request.form.get("away_derby")),
            "home_rivalry": bool(request.form.get("home_rivalry")),
            "away_rivalry": bool(request.form.get("away_rivalry")),
            "home_injury":  int(request.form.get("home_injury", 0)),
            "away_injury":  int(request.form.get("away_injury", 0)),
        })

        if home and away and home != away:
            features = get_features(home, away, latest_season, states, h2h_history)

            home_mot = (form_vals["home_stake"]
                        + (DERBY_BONUS   if form_vals["home_derby"]   else 0)
                        + (RIVALRY_BONUS if form_vals["home_rivalry"] else 0))
            away_mot = (form_vals["away_stake"]
                        + (DERBY_BONUS   if form_vals["away_derby"]   else 0)
                        + (RIVALRY_BONUS if form_vals["away_rivalry"] else 0))
            mot_diff = home_mot - away_mot
            inj_diff = form_vals["away_injury"] - form_vals["home_injury"]

            prediction = predict_probs(features, mot_diff, inj_diff, model)

    return render_template(
        "predict.html",
        active="predict",
        teams=teams,
        form=form_vals,
        stake_options=STAKE_OPTIONS,
        derby_bonus=DERBY_BONUS,
        rivalry_bonus=RIVALRY_BONUS,
        features=features,
        prediction=prediction,
        mot_diff=mot_diff,
        inj_diff=inj_diff,
        min_mp=config.MIN_MATCHES_FOR_PPG,
        model_weights=model["manual_weights"],
    )


# ── export routes ─────────────────────────────────────────────────────────────

@app.route("/export/matches")
def export_matches():
    return Response(
        db.export_matches_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=raw_matches.csv"},
    )


@app.route("/export/calibration")
def export_calibration():
    return Response(
        db.export_calibration_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=calibration_table.csv"},
    )


# ── FootyStats column aliases ─────────────────────────────────────────────────

_COL = {
    "id":         ["id", "match_id"],
    "date":       ["date_GMT", "date", "Date"],
    "status":     ["status", "Status", "match_status"],
    "home_team":  ["home_team_name", "home_team", "Home Team"],
    "away_team":  ["away_team_name", "away_team", "Away Team"],
    "home_goals": ["home_team_goal_count", "home_goals", "HG", "home_score"],
    "away_goals": ["away_team_goal_count", "away_goals", "AG", "away_score"],
    "round":      ["Game Week", "game_week", "round", "Round", "matchday"],
}

_FOOTYSTATS_COMPLETE = {"complete", "complete (not inc. extra time)", "1", "true"}


def _pick(row, key):
    for col in _COL[key]:
        if col in row:
            return row[col]
    return None


def _footystats_to_raw(rows, season):
    out = []
    for r in rows:
        home = _pick(r, "home_team")
        away = _pick(r, "away_team")
        if not home or not away:
            continue

        raw_status = (_pick(r, "status") or "").strip().lower()
        status = "FT" if raw_status in _FOOTYSTATS_COMPLETE else "NS"

        hg = _pick(r, "home_goals")
        ag = _pick(r, "away_goals")
        try:
            hg = int(float(hg)) if hg not in (None, "", "None") else None
            ag = int(float(ag)) if ag not in (None, "", "None") else None
        except (ValueError, TypeError):
            hg, ag = None, None

        date   = (_pick(r, "date") or "").strip()
        raw_id = _pick(r, "id")
        if raw_id:
            fixture_id = f"fs_{season}_{raw_id}"
        else:
            h = hashlib.md5(f"{season}{date}{home}{away}".encode()).hexdigest()[:8]
            fixture_id = f"fs_{h}"

        out.append({
            "fixture_id":   fixture_id,
            "season":       season,
            "date":         date,
            "round":        _pick(r, "round") or "",
            "status":       status,
            "home_team":    home,
            "home_team_id": "",
            "away_team":    away,
            "away_team_id": "",
            "home_goals":   hg,
            "away_goals":   ag,
        })
    return out


def _check_cols(header):
    missing = []
    for key in ("home_team", "away_team", "date"):
        if not any(c in header for c in _COL[key]):
            missing.append(key)
    return missing


@app.route("/import/thesportsdb", methods=["POST"])
def import_thesportsdb():
    import pull_thesportsdb as sdb
    season = int(request.form.get("season", 2025))
    sdb_result = None
    try:
        rows = sdb.pull_season(season)
        if not rows:
            sdb_result = {"error": "No data returned from TheSportsDB for that season."}
        else:
            added, skipped = db.insert_matches(rows)
            if added > 0:
                subprocess.run([sys.executable, "build_features.py"], check=True)
            rounds = len({r["round"] for r in rows})
            total = len(db.fetch_all_matches())
            sdb_result = {"added": added, "skipped": skipped,
                          "total": total, "rounds": rounds}
    except Exception as e:
        sdb_result = {"error": str(e)}

    return render_template("import.html", active="import",
                           result=None, sdb_result=sdb_result)


@app.route("/import", methods=["GET", "POST"])
def import_data():
    result = None

    if request.method == "POST":
        f      = request.files.get("csv_file")
        season = int(request.form.get("season", 2025))

        if not f or not f.filename:
            result = {"error": "No file selected."}
        else:
            try:
                text   = f.read().decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(text))
                fs_rows = list(reader)
                header  = reader.fieldnames or []

                missing = _check_cols(header)
                if missing:
                    result = {
                        "error": f"Could not find required columns for: {', '.join(missing)}. "
                                 "The column mapping may need updating for this FootyStats export.",
                        "detected_cols": header,
                    }
                else:
                    new_rows = _footystats_to_raw(fs_rows, season)
                    added, skipped = db.insert_matches(new_rows)

                    sample = []
                    if added > 0:
                        sample = new_rows[:8]
                        subprocess.run([sys.executable, "build_features.py"], check=True)

                    total = len(db.fetch_all_matches())
                    result = {
                        "added":   added,
                        "skipped": skipped,
                        "total":   total,
                        "sample":  sample,
                    }

            except Exception as e:
                result = {"error": str(e)}

    return render_template("import.html", active="import", result=result, sdb_result=None)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

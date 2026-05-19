# Ligat Ha'Al Match Predictor — Design & Decision Log

This file is the **why**. If you (or another Claude) are picking this project up,
read this first, then `STATE.md`. The reasoning here was built up slowly and
deliberately — please don't silently reverse these decisions. If something here
looks wrong, raise it explicitly rather than "helpfully" changing course.

## Goal

A local web portal that predicts Israeli Premier League (Ligat Ha'Al) match
outcomes as **1X2 probabilities** (home win / draw / away win), to support
betting decisions. Built slowly, one parameter at a time, favouring flat,
debuggable solutions over clever architecture.

## Output design

- The model produces a single **advantage score** as an intermediate value,
  then a conversion function maps that score to three 1X2 probabilities.
- 1X2 was chosen over (a) a single advantage number — not useful for betting on
  its own — and (b) goals/Poisson — a different model class the parameters
  aren't built for.

## The six parameters

Each was discussed individually. They split into two structural types, and the
type determines how the parameter enters the formula. **Do not collapse these
into one combined score** — that distinction is the whole point.

| Parameter | Measure | Type | Input source |
|-----------|---------|------|--------------|
| Table position | PPG difference between teams | Comparative | Automatic (API) |
| Recent form | Opponent-adjusted, exponentially-decayed results over last 5–6 matches | Comparative | Automatic (API) |
| Home advantage | Constant bias toward home side (~0.3–0.4 pts) | Bias | Constant |
| Head-to-head | Small correction, fresh window only, only matters when quality is close | Comparative | Automatic (API) |
| Injuries / absences | Manual 0–10 "absence severity" rating, anchored to fixed reference points | Bias (difference enters model) | Manual |
| Motivation | 3-question questionnaire → score | Comparative (difference enters model) | Manual |

### Key per-parameter reasoning

- **Table position**: use PPG (normalises for matches played), not raw points
  and not ordinal league position. Ordinal position loses the size of gaps and
  is non-linear (mid-table is congested).
- **Recent form**: defined as a *standalone* value (opponent-adjusted, decayed),
  NOT as a deviation from PPG. The deviation approach is more elegant but
  creates a chained dependency that's hard to debug. Overlap with PPG is
  intentionally left to be sorted out at the calibration stage, where w_form
  and w_table are tuned together.
- **Home advantage**: behaves as a **bias**, not a comparative parameter — it's
  added to the home side regardless of team quality. In the regression it is
  captured by the **intercept** — it is deliberately NOT a column in the
  feature table.
- **Head-to-head**: the user initially thought this was very important; we
  concluded it is the most over-rated parameter. It's largely a *symptom* of
  quality gaps already captured by PPG/form. Given a low, near-symbolic weight;
  expected to converge near zero at calibration. Israeli league specifics make
  it worse (fast squad turnover, small sample, playoff format).
- **Injuries**: a precise minutes-weighted model is false precision because
  Israeli league injury reporting is unreliable. Chosen approach is a manual
  0–10 rating with fixed anchor points (e.g. one key player no real replacement
  = 4–5; multiple core players incl. critical positions = 8–9). Defence/keeper
  weighted more heavily than attack. Define as "what changed since last match"
  to avoid overlap with form.
- **Motivation**: manual questionnaire with fixed-scale answers, applies ONLY
  to this parameter. Three questions: (1) what's at stake — title/survival 10,
  Europe 7, playoff spot 6, mid-table 5, nothing 2; (2) derby? +constant;
  (3) specific historical rivalry? +constant. Score = sum. The "derby/rivalry"
  axis was originally raised by the user as a throwaway "bonus" — it turned out
  to be the second structural axis of motivation, distinct from "what's at
  stake". Allow low scores (1–2): a team with nothing to play for is a strong
  signal, not a default-5.

## Calibration approach (hybrid — important)

- Calibration = **multinomial logistic regression** (three outcomes) on a table
  of historical matches, each row holding the parameter values **as they stood
  the moment before kickoff** and the actual result.
- Only the **automatic** parameters (PPG diff, form diff, H2H diff) can be
  calibrated this way — there is no historical record of motivation or injury
  ratings to reconstruct.
- Therefore the initial model is **partially calibrated**: 3 parameters tuned
  statistically, motivation + injuries enter with **manual initial weights**,
  tuned by hand over the season as questionnaire data accumulates.
- Don't guess weights before the model runs end-to-end. Calibrating a model
  that hasn't run is premature optimisation.

## The point-in-time rule (the biggest technical trap)

To calibrate, every historical match must carry the parameter values **as they
were just before that match — never using the match itself or anything later.**

The classic mistake: using a season's *final* PPG table to "predict" a
mid-season match. That is **data leakage** — the model looks brilliant in
calibration and then fails in real life. `build_features.py` reconstructs each
match's state by walking the season forward chronologically and computing only
from prior matches. This was verified with a synthetic-data test
(`_test_features.py`).

## Architecture decisions

- **Files, not a database.** ~800–960 matches (~1000 rows). A DB server is
  exactly the kind of complexity we're avoiding at this scale, and CSVs can be
  eyeballed in Excel / read in git. If it ever outgrows this (multi-user portal,
  or richer relational questionnaire data), move to **SQLite** — still one file,
  no server, built into Python. NOT Postgres, and not yet.
- **The API is not part of the running model.** `pull_data.py` runs rarely
  (once for history, then weekly for new results) and writes CSVs. The portal
  *reads* CSVs. The portal must never re-pull the API on page load.
- Deployment boundary: the **data pipeline** (`pull_data`, `build_features`,
  `calibrate`) is a batch job that writes CSVs; the **portal** (`app.py`) is the
  long-running web service that reads them. Same repo, separate concerns.

## Chosen data source

- **API-Football** (v3, `v3.football.api-sports.io`) — most comprehensive, has
  several seasons of history, free tier ~100 calls/day (we need ~4 for a full
  history pull). FootyStats is a viable backup (direct CSV export).
- Pull **3–4 recent seasons** only. Enough matches to calibrate on (~240/season)
  but recent enough to still be "the same league". Don't go below 2 or above 5.

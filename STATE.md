# Project State — where things stand

Read `DESIGN.md` first for the *why*. This file is the *where we are* and
*what's next*.

## Pipeline stages

| Stage | File | Status |
|-------|------|--------|
| 1. Pull historical fixtures from API-Football | `pull_data.py` | **Done** — 3 seasons (2022–2024), 720 matches |
| 1b. Pull current season from TheSportsDB | `pull_thesportsdb.py` | **Done** — 2025/26, 240 matches, 233 completed |
| 2. Build point-in-time calibration table | `build_features.py` | **Done** — 953 rows, 868 reliable |
| 3. Multinomial logistic regression for weights | `calibrate.py` | **Done** — trained on 868 rows across 4 seasons |
| 4. Local web portal | `app.py` | **Done and running** — standings, predict, import pages |
| 5. Run on real fixtures, hand-tune manual weights | — | Not started |

## What exists right now

### Data files (in `data/`)
- `raw_matches.csv` — 960 rows total: 720 from API-Football (seasons 2022–2024) + 240 from TheSportsDB (season 2025/26)
- `calibration_table.csv` — 953 completed matches with point-in-time features
- `model_weights.json` — calibrated coefficients + manual weight placeholders

### Python files
- `config.py` — `LEAGUE_ID = 383` (set), `SEASONS = [2022, 2023, 2024]`, `MODEL_WEIGHTS` path added
- `pull_data.py` — API-Football puller (free tier: seasons 2022–2024 only; season 2025 blocked)
- `pull_thesportsdb.py` — TheSportsDB puller, free, no key needed. Pulls round-by-round with 2.5s sleep (30 req/min limit). Has retry logic for 429 errors. Team name mapping handles 4 spelling differences between sources. Run: `python pull_thesportsdb.py 2025`
- `build_features.py` — unchanged except fixture_id sort changed from `int()` to `str()` to support `sdb_` prefixed IDs from TheSportsDB
- `calibrate.py` — multinomial logistic regression, drops early-season rows, does leave-one-season-out CV, saves `model_weights.json`
- `app.py` — Flask portal on port 5000. Three pages: Standings (`/`), Predict (`/predict`), Import Data (`/import`)
- `_test_features.py` — synthetic data leakage test; still valid (uses numeric fixture IDs, unaffected by the str() fix)

### Templates (in `templates/`)
- `base.html` — shared layout, nav: Standings · Predict · Import Data
- `index.html` — league table with W/D/L/GF/GA/Pts/PPG/Form(last5), team picker to go to predict
- `predict.html` — automatic features display + motivation questionnaire + injury inputs + probability bar
- `import.html` — two sections: TheSportsDB terminal command guide + FootyStats CSV upload

## Current model performance (4 seasons)

| Metric | Value |
|--------|-------|
| Training accuracy | 47.6% (baseline 39.4%) |
| Training log-loss | 1.021 |
| CV mean accuracy | 47.2% |
| CV 2025/26 season | 51.4% — strongest fold |

Coefficients (H class): intercept +0.18, ppg_diff +0.405, form_diff +0.065, h2h_diff +0.049

## Data source notes

- **API-Football** (key: set via `APIFOOTBALL_KEY` env var): free tier covers 2022–2024 only. Season 2025 returns "Free plans do not have access to this season".
- **TheSportsDB**: free, key is literally `"123"`, no registration. League ID `4644`. Rate limit 30 req/min — script uses 2.5s sleep + 429 retry. Run weekly after new results to update.
- **FootyStats**: CSV download requires paid account — not viable as free source.

## Team name mapping (TheSportsDB → canonical API-Football names)

Stored in `pull_thesportsdb.py` as `NAME_MAP`:
```
"FC Ashdod"                  → "Ashdod"
"Hapoel Be'er Sheva"         → "Hapoel Beer Sheva"
"Hapoel Ironi Kiryat Shmona" → "Ironi Kiryat Shmona"
"Hapoel Tel-Aviv"            → "Hapoel Tel Aviv"
```
`Hapoel Petah Tikva` and `Hapoel Jerusalem` are genuinely different teams from prior seasons — no mapping needed.

## Weekly update workflow

```bash
python pull_thesportsdb.py 2025   # adds new completed matches (skips existing)
python build_features.py           # rebuilds calibration table
python calibrate.py                # re-fits model weights
python app.py                      # start portal on http://localhost:5000
```

## Next actions

1. **Hand-tune manual weights** — `motivation_diff` and `injury_diff` are both `0.0` in `data/model_weights.json`. Start using the portal for real predictions, then tune these values by hand over the season. Suggested starting range: 0.1–0.3 (interpreted as: 1 unit of motivation/injury advantage = X × ppg_diff effect per class).
2. **Verify team names in 2025/26 are consistent** — TheSportsDB names Ironi Kiryat Shmona correctly but H2H history from API-Football uses the same name, so H2H should carry over fine.
3. **`_test_features.py`** — the leakage test still passes (uses numeric fixture IDs, doesn't exercise the `str()` sort path). Worth keeping as-is since it tests the logic, not the ID format.

## Open questions (from original design, still parked)

- Exact form of the conversion function from advantage score → 1X2 (currently the multinomial softmax is the conversion — revisit only if a single-score intermediate becomes useful)
- Whether to move from CSV to SQLite once the portal stores questionnaire data (not urgent)
- Initial manual weights for motivation and injuries (deferred until real predictions accumulate)

## Watch out for

- **Data leakage** — any change to `build_features.py` must preserve point-in-time rule. Re-run `_test_features.py` after touching it.
- **fixture_id format** — API-Football IDs are plain integers; TheSportsDB IDs are `sdb_{idEvent}`. Both `build_features.py` and `app.py` now sort by `str(fixture_id)`. Do not revert to `int()`.
- **TheSportsDB rate limit** — 30 req/min. Don't run `pull_thesportsdb.py` multiple times in quick succession or the 429 retry logic will kick in (30s, 60s, 90s waits).
- **Don't reverse design decisions** — H2H low weight, files over DB, API-not-in-running-model, comparative-vs-bias split. All deliberate. See `DESIGN.md`.

# Ligat Ha'Al Match Predictor

A local web portal that predicts Israeli Premier League match outcomes as
1X2 probabilities (home win / draw / away win).

## Start here

1. **`DESIGN.md`** — every design decision and the reasoning behind it. Read first.
2. **`STATE.md`** — current progress and the next concrete steps.

## Project layout

```
ligat-haal-predictor/
├── DESIGN.md            # decision log — the "why"
├── STATE.md             # progress + next steps — the "where"
├── README.md            # this file
├── config.py            # API key (from env var), league id, seasons, params
├── pull_data.py         # stage 1: API-Football -> data/raw_matches.csv
├── build_features.py    # stage 2: -> data/calibration_table.csv (point-in-time)
├── _test_features.py    # synthetic-data leakage test for build_features.py
└── data/                # generated CSVs (not in version control)
```

`calibrate.py` (stage 3) and `app.py` (stage 4, the portal) are not built yet.

## Setup

```bash
# 1. get a free key at https://www.api-football.com/
# 2. provide it via environment variable (never hardcode it)
export APIFOOTBALL_KEY="your_key_here"        # Windows cmd: set APIFOOTBALL_KEY=your_key_here

# 3. first run lists Israeli leagues — copy the Premier League id into config.py
python pull_data.py

# 4. second run pulls the configured seasons
python pull_data.py

# 5. build the calibration table
python build_features.py

# verify the feature builder is leak-free at any time
python _test_features.py
```

No third-party packages required so far — standard library only.

## Principles (see DESIGN.md for full reasoning)

- Built slowly, one parameter at a time; flat and debuggable over clever.
- Six parameters, split into **comparative** and **bias** types — the split
  drives how each enters the formula.
- **Point-in-time discipline**: features are reconstructed as they stood before
  each match, never using the result or anything later. This prevents data
  leakage.
- **Files, not a database**, at this scale. SQLite later only if it's actually
  needed.
- **The API is not part of the running model** — it's a batch data source.

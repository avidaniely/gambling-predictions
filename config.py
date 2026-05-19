"""
Configuration for the Ligat Ha'Al predictor.

The API key is read from an environment variable, NOT stored here — so this
file is safe to keep in version control. Do not hardcode the key.
"""
import os

# --- API access -------------------------------------------------------------
# Get a free key at https://www.api-football.com/  then, before running:
#   export APIFOOTBALL_KEY="your_key_here"
API_KEY = os.environ.get("APIFOOTBALL_KEY", "")
API_BASE = "https://v3.football.api-sports.io"

# --- What to pull -----------------------------------------------------------
# League id for the Israeli Premier League on API-Football.
# Leave as None on the first run — pull_data.py will look it up and print it,
# then you paste the right id back in here.
LEAGUE_ID = 383

# Seasons are identified by their STARTING year (2023 == season 2023/24).
# 3-4 recent seasons is the sweet spot we agreed on: enough matches to
# calibrate on, recent enough to still be "the same league".
SEASONS = [2022, 2023, 2024]

# --- Files ------------------------------------------------------------------
DATA_DIR = "data"
RAW_MATCHES = f"{DATA_DIR}/raw_matches.csv"
CALIBRATION_TABLE = f"{DATA_DIR}/calibration_table.csv"
MODEL_WEIGHTS = f"{DATA_DIR}/model_weights.json"

# --- Feature parameters -----------------------------------------------------
FORM_WINDOW = 5                 # matches in the recent-form window
FORM_DECAY = 0.8                # exponential decay; most recent match weight = 1.0
H2H_SEASONS_BACK = 1            # prior seasons of H2H to consider (plus current)
MIN_MATCHES_FOR_PPG = 3         # below this, a team's PPG is flagged unreliable
LEAGUE_AVG_PPG_FALLBACK = 1.35  # used early in a season before enough data exists

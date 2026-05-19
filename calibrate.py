"""
Stage 3: fit multinomial logistic regression weights on the calibration table.

Fits coefficients for the three automatic parameters (ppg_diff, form_diff,
h2h_diff). Home advantage is captured by the intercept — it is not a feature.
Motivation and injuries are not calibrated here; they have no historical
record. They enter the prediction later as extra linear terms with manual
weights (see the note in model_weights.json).

Early-season rows (either team below MIN_MATCHES_FOR_PPG) are dropped before
fitting — their ppg/form features are unreliable.

Outputs:
    data/model_weights.json  — coefficients + intercepts, consumed by app.py

Usage:
    python calibrate.py
"""
import csv
import json
import sys
from collections import Counter, defaultdict

try:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, log_loss
except ImportError:
    sys.exit(
        "calibrate.py needs scikit-learn and numpy.\n"
        "Install them:  pip install scikit-learn numpy"
    )

import config

FEATURES = ["ppg_diff", "form_diff", "h2h_diff"]


def load_reliable_rows():
    try:
        with open(config.CALIBRATION_TABLE, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        sys.exit(f"{config.CALIBRATION_TABLE} not found — run build_features.py first.")

    reliable, dropped = [], 0
    for r in rows:
        if (int(r["home_matches_played"]) < config.MIN_MATCHES_FOR_PPG
                or int(r["away_matches_played"]) < config.MIN_MATCHES_FOR_PPG
                or not r["ppg_diff"] or not r["form_diff"]):
            dropped += 1
            continue
        reliable.append(r)

    print(f"Rows: {len(rows)} total, {dropped} early-season dropped, "
          f"{len(reliable)} used for calibration.")
    return reliable


def to_arrays(rows):
    X = np.array([[float(r[f]) for f in FEATURES] for r in rows])
    y = np.array([r["result"] for r in rows])
    seasons = np.array([int(r["season"]) for r in rows])
    return X, y, seasons


def fit_model(X, y):
    model = LogisticRegression(
        solver="lbfgs", max_iter=1000, C=1.0, random_state=42,
    )
    model.fit(X, y)
    return model


def report(model, X, y, seasons):
    classes = list(model.classes_)
    preds = model.predict(X)
    proba = model.predict_proba(X)
    acc = accuracy_score(y, preds)
    ll = log_loss(y, proba, labels=classes)
    baseline = max(Counter(y).values()) / len(y)

    print(f"\n--- Full-data fit ({len(y)} matches) ---")
    print(f"  Accuracy : {acc:.3f}  (always-predict-most-common baseline: {baseline:.3f})")
    print(f"  Log-loss : {ll:.4f}")

    print(f"\n--- Coefficients ---")
    for cls, coef, icpt in zip(classes, model.coef_, model.intercept_):
        terms = "  ".join(f"{f}={c:+.4f}" for f, c in zip(FEATURES, coef))
        print(f"  {cls}: intercept={icpt:+.4f}  {terms}")

    print(f"\n--- Confusion matrix (rows=actual, cols=predicted) ---")
    cm = defaultdict(lambda: defaultdict(int))
    for actual, pred in zip(y, preds):
        cm[actual][pred] += 1
    srt = sorted(classes)
    print("         " + "  ".join(f"{c:>5}" for c in srt))
    for actual in srt:
        print(f"  {actual}:   " + "  ".join(f"{cm[actual][p]:>5}" for p in srt))

    print(f"\n--- Leave-one-season-out cross-validation ---")
    cv_accs, cv_lls = [], []
    for held_out in sorted(set(seasons)):
        train = seasons != held_out
        test = seasons == held_out
        cv_model = fit_model(X[train], y[train])
        cv_proba = cv_model.predict_proba(X[test])
        cv_preds = cv_model.predict(X[test])
        a = accuracy_score(y[test], cv_preds)
        l = log_loss(y[test], cv_proba, labels=cv_model.classes_)
        cv_accs.append(a)
        cv_lls.append(l)
        print(f"  Hold out {held_out}/{held_out+1}: "
              f"accuracy={a:.3f}  log-loss={l:.4f}  n={test.sum()}")
    print(f"  Mean:              "
          f"accuracy={sum(cv_accs)/len(cv_accs):.3f}  "
          f"log-loss={sum(cv_lls)/len(cv_lls):.4f}")


def save_weights(model, n_trained):
    classes = list(model.classes_)
    weights = {
        "classes": classes,
        "features": FEATURES,
        "coef": {
            cls: dict(zip(FEATURES, coef.tolist()))
            for cls, coef in zip(classes, model.coef_)
        },
        "intercept": dict(zip(classes, model.intercept_.tolist())),
        "n_trained": n_trained,
        "manual_weights": {
            "motivation_diff": 0.0,
            "injury_diff": 0.0,
            "_note": (
                "motivation_diff and injury_diff are (home - away) scores. "
                "They are added as extra linear terms to every class score "
                "before the softmax, using the coefficient here. "
                "Start at 0.0 and tune by hand over the season."
            ),
        },
    }
    with open(config.MODEL_WEIGHTS, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2)
    print(f"\nWeights saved to {config.MODEL_WEIGHTS}")


if __name__ == "__main__":
    rows = load_reliable_rows()
    X, y, seasons = to_arrays(rows)
    model = fit_model(X, y)
    report(model, X, y, seasons)
    save_weights(model, len(rows))

TRANSLATIONS = {
    "en": {
        # Site / nav
        "site_title":       "Ligat Ha'Al Predictor",
        "nav_standings":    "Standings",
        "nav_predict":      "Predict",
        "nav_import":       "Import Data",
        "lang_toggle":      "עב",
        "lang_toggle_title":"Switch to Hebrew",

        # Standings
        "standings_title":  "{season}/{next} Season Standings",
        "col_pos":          "#",
        "col_team":         "Team",
        "col_played":       "P",
        "col_wins":         "W",
        "col_draws":        "D",
        "col_losses":       "L",
        "col_gf":           "GF",
        "col_ga":           "GA",
        "col_pts":          "Pts",
        "col_ppg":          "PPG",
        "col_form":         "Form (last 5)",

        # Predict — form
        "predict_title":    "Prediction Form",
        "home_team":        "Home Team",
        "away_team":        "Away Team",
        "select_team":      "— select —",

        # Match data table
        "match_data_head":  "Match Data",
        "factor_col":       "Factor",
        "home_col":         "🏠 Home",
        "away_col":         "✈ Away",
        "edge_col":         "Edge",

        "factor_ppg":       "Season PPG",
        "ppg_tooltip":      "Points Per Game — average league points earned per match this season (Win=3, Draw=1, Loss=0). Higher = stronger team on paper.",
        "factor_form":      "Recent form",
        "form_subtitle":    "last 5, opp-adjusted",
        "form_tooltip":     "Average points per match over the last 5 games, weighted so recent results count more (decay 0.8) and adjusted for opponent strength.",
        "factor_h2h":       "Head-to-head",
        "h2h_tooltip":      "Average points per match in recent meetings. Only current + last season counted — older results ignored as squads change.",
        "no_meetings":      "No recent meetings",
        "h2h_avg":          "Home averaged {diff} pts/match vs away",
        "h2h_meeting":      "recent meeting",
        "h2h_meetings":     "recent meetings",
        "early_season_warn":"⚠ early season (<{min_mp} matches)",
        "edge_home":        "→ Home",
        "edge_away":        "→ Away",
        "edge_even":        "≈ Even",
        "edge_no_data":     "≈ No data",

        # Motivation
        "motivation_head":  "Motivation",
        "stake_label":      "What's at stake?",
        "match_context_head": "Match Context",
        "derby_label":      "Derby match (+{bonus} to both teams)",
        "rivalry_label":    "Historical rivalry (+{bonus} to both teams)",
        "home_prefix":      "🏠 Home",
        "away_prefix":      "✈ Away",

        # Stake options
        "stake_10":         "Title race / Relegation survival",
        "stake_7":          "European qualification",
        "stake_6":          "Playoff spot",
        "stake_5":          "Mid-table (no clear objective)",
        "stake_2":          "Nothing at stake",

        # Injuries
        "injury_head":      "Injury / Absence Severity",
        "home_injury_lbl":  "🏠 Home team absence severity (0–10)",
        "away_injury_lbl":  "✈ Away team absence severity (0–10)",
        "injury_hint":      "0 = full squad · 2–3 = fringe players out · 4–5 = one key player, no replacement · 7–8 = multiple starters incl. key position · 9–10 = crisis",
        "injury_hint2":     "Rate what changed since their last match to avoid double-counting form.",

        "calc_btn":         "Calculate Prediction",

        # Result
        "result_title":     "Prediction: {home} vs {away}",
        "home_win":         "Home win",
        "draw":             "Draw",
        "away_win":         "Away win",

        # Breakdown — factor names
        "factor_home_adv":      "Home advantage",
        "factor_ppg_strength":  "Table strength (PPG)",
        "factor_form_bd":       "Recent form",
        "factor_h2h_bd":        "Head-to-head",
        "factor_motivation":    "Motivation",
        "factor_injuries":      "Injuries / absences",

        # Breakdown
        "breakdown_title":  "How this prediction was calculated",
        "bd_factor":        "Factor",
        "bd_values":        "Values",
        "bd_direction":     "Direction",
        "bd_explanation":   "Explanation",
        "bd_footer":        "Logit scores are summed and passed through softmax to produce H / D / A percentages. Positive logit → boosts home win; negative → boosts away win.",
        "bd_inactive":      "inactive",
        "bd_home":          "↑ home",
        "bd_away":          "↓ away",
        "bd_neutral":       "≈ neutral",

        # Import page
        "import_pull_title":"Pull Season Data",
        "import_pull_desc": "Pulls results from TheSportsDB (free, no sign-up), rebuilds the calibration table and re-fits the model. Run weekly to keep predictions current. Takes ~6 minutes due to API rate limits.",
        "season_label":     "Season",
        "pull_btn":         "Pull",
        "running_btn":      "Running…",
        "connecting":       "Connecting…",
        "waiting":          "(waiting…)",
        "network_error":    "(network error — retrying…)",
        "already_running":  "A pull is already running — showing live progress below.",
        "refresh_done":     "✓ Done — reload to see updated standings and predictions.",
        "reload_btn":       "Reload page",
        "error_btn":        "Error — try again",

        "recent_title":     "Last 20 Matches in Database",
        "no_matches":       "No completed matches in database yet.",
        "date_col":         "Date",
        "season_col":       "Season",
        "score_col":        "Score",

        "export_title":     "Export Data (CSV)",
        "export_desc":      "Download the current database contents as CSV files.",

        "import_csv_title": "Import CSV (manual fallback)",
        "import_csv_desc":  "If you have a FootyStats CSV from a paid account, you can import it here.",
        "csv_file_label":   "CSV file",
        "season_year_lbl":  "Season start year",
        "import_btn":       "Import",

        "new_added":        "{n} new matches added",
        "already_existed":  "{n} already existed",
        "total_db":         "{n} total in database",
        "calib_rebuilt":    "Calibration table rebuilt automatically.",
        "no_new_matches":   "No new matches added — all rows already exist.",
        "col_detected":     "Columns in your file:",
    },

    "he": {
        # Site / nav
        "site_title":       "מנבא ליגת העל",
        "nav_standings":    "טבלה",
        "nav_predict":      "ניבוי",
        "nav_import":       "ייבוא נתונים",
        "lang_toggle":      "EN",
        "lang_toggle_title":"Switch to English",

        # Standings
        "standings_title":  "טבלת עונת {season}/{next}",
        "col_pos":          "#",
        "col_team":         "קבוצה",
        "col_played":       "מ׳",
        "col_wins":         "נ׳",
        "col_draws":        "ת׳",
        "col_losses":       "ה׳",
        "col_gf":           "שנ׳",
        "col_ga":           "שנ״נ",
        "col_pts":          "נק׳",
        "col_ppg":          "נק׳/מ׳",
        "col_form":         "פורמה (5 אחרונים)",

        # Predict — form
        "predict_title":    "טופס ניבוי",
        "home_team":        "קבוצת בית",
        "away_team":        "קבוצת חוץ",
        "select_team":      "— בחר —",

        # Match data table
        "match_data_head":  "נתוני המשחק",
        "factor_col":       "גורם",
        "home_col":         "🏠 בית",
        "away_col":         "✈ חוץ",
        "edge_col":         "יתרון",

        "factor_ppg":       "נק׳ למשחק (עונה)",
        "ppg_tooltip":      "נקודות למשחק — ממוצע הנקודות לליגה לכל משחק בעונה זו (ניצחון=3, תיקו=1, הפסד=0). גבוה יותר = קבוצה חזקה יותר על הנייר.",
        "factor_form":      "פורמה אחרונה",
        "form_subtitle":    "5 אחרונים, מותאם ליריב",
        "form_tooltip":     "ממוצע נקודות ב-5 משחקים אחרונים, עם עדיפות למשחקים אחרונים (דעיכה 0.8) ומותאם לחוזק היריב.",
        "factor_h2h":       "עימותים ישירים",
        "h2h_tooltip":      "ממוצע נקודות למשחק בעימותים בין הקבוצות. רק העונה הנוכחית ועונה קודמת נחשבות — עונות ישנות יותר נמחקות.",
        "no_meetings":      "אין עימותים אחרונים",
        "h2h_avg":          "קבוצת הבית ממוצע {diff} נק׳/מ׳ מעל קבוצת החוץ",
        "h2h_meeting":      "עימותים אחרונים",
        "h2h_meetings":     "עימותים אחרונים",
        "early_season_warn":"⚠ תחילת עונה (<{min_mp} משחקים)",
        "edge_home":        "← בית",
        "edge_away":        "← חוץ",
        "edge_even":        "≈ שווה",
        "edge_no_data":     "≈ אין נתונים",

        # Motivation
        "motivation_head":  "מוטיבציה",
        "stake_label":      "מה על הכף?",
        "match_context_head": "הקשר המשחק",
        "derby_label":      "דרבי (+{bonus} לשתי הקבוצות)",
        "rivalry_label":    "יריבות היסטורית (+{bonus} לשתי הקבוצות)",
        "home_prefix":      "🏠 בית",
        "away_prefix":      "✈ חוץ",

        # Stake options
        "stake_10":         "מרוץ לאליפות / מאבק הישרדות",
        "stake_7":          "כרטיס לאירופה",
        "stake_6":          "מקום בפלייאוף",
        "stake_5":          "אמצע טבלה (ללא מטרה ברורה)",
        "stake_2":          "אין על הכף",

        # Injuries
        "injury_head":      "חומרת פציעות / היעדרויות",
        "home_injury_lbl":  "🏠 חומרת היעדרויות קבוצת בית (0–10)",
        "away_injury_lbl":  "✈ חומרת היעדרויות קבוצת חוץ (0–10)",
        "injury_hint":      "0 = הרכב מלא · 2–3 = שחקני שוליים חסרים · 4–5 = שחקן מפתח אחד ללא מחליף · 7–8 = כמה שחקני בסיס כולל עמדה קריטית · 9–10 = משבר",
        "injury_hint2":     "דרג מה שהשתנה מהמשחק האחרון כדי להימנע מכפל ספירה עם הפורמה.",

        "calc_btn":         "חשב ניבוי",

        # Result
        "result_title":     "ניבוי: {home} נגד {away}",
        "home_win":         "ניצחון בית",
        "draw":             "תיקו",
        "away_win":         "ניצחון חוץ",

        # Breakdown — factor names
        "factor_home_adv":      "יתרון בית",
        "factor_ppg_strength":  "עוצמת טבלה (נק׳/מ׳)",
        "factor_form_bd":       "פורמה אחרונה",
        "factor_h2h_bd":        "עימותים ישירים",
        "factor_motivation":    "מוטיבציה",
        "factor_injuries":      "פציעות / היעדרויות",

        # Breakdown
        "breakdown_title":  "איך חושב הניבוי",
        "bd_factor":        "גורם",
        "bd_values":        "ערכים",
        "bd_direction":     "כיוון",
        "bd_explanation":   "הסבר",
        "bd_footer":        "הציונים מסוכמים ועוברים דרך softmax לקבלת אחוזי בית / תיקו / חוץ. ציון חיובי מגביר הסתברות לניצחון בית; שלילי — לניצחון חוץ.",
        "bd_inactive":      "לא פעיל",
        "bd_home":          "↑ בית",
        "bd_away":          "↓ חוץ",
        "bd_neutral":       "≈ שווה",

        # Import page
        "import_pull_title":"עדכון נתוני עונה",
        "import_pull_desc": "שולף תוצאות מ-TheSportsDB (חינם, ללא הרשמה), בונה מחדש את טבלת הכיול ומכייל מחדש את המודל. הרץ שבועי לעדכון. אורך כ-6 דקות.",
        "season_label":     "עונה",
        "pull_btn":         "משוך",
        "running_btn":      "רץ…",
        "connecting":       "מתחבר…",
        "waiting":          "(ממתין…)",
        "network_error":    "(שגיאת רשת — מנסה שוב…)",
        "already_running":  "משיכה כבר פועלת — מציג התקדמות חיה למטה.",
        "refresh_done":     "✓ הסתיים — רענן לצפות בטבלה ובניבויים המעודכנים.",
        "reload_btn":       "רענן עמוד",
        "error_btn":        "שגיאה — נסה שוב",

        "recent_title":     "20 המשחקים האחרונים בבסיס הנתונים",
        "no_matches":       "אין משחקים שהסתיימו בבסיס הנתונים עדיין.",
        "date_col":         "תאריך",
        "season_col":       "עונה",
        "score_col":        "תוצאה",

        "export_title":     "ייצוא נתונים (CSV)",
        "export_desc":      "הורד את תוכן בסיס הנתונים כקבצי CSV.",

        "import_csv_title": "ייבוא CSV (גיבוי ידני)",
        "import_csv_desc":  "אם יש לך CSV מ-FootyStats עם חשבון בתשלום, אפשר לייבא כאן.",
        "csv_file_label":   "קובץ CSV",
        "season_year_lbl":  "שנת תחילת עונה",
        "import_btn":       "ייבא",

        "new_added":        "{n} משחקים חדשים נוספו",
        "already_existed":  "{n} כבר קיימים",
        "total_db":         "{n} סה״כ בבסיס הנתונים",
        "calib_rebuilt":    "טבלת הכיול נבנתה מחדש אוטומטית.",
        "no_new_matches":   "לא נוספו משחקים חדשים — כל השורות כבר קיימות.",
        "col_detected":     "עמודות שזוהו בקובץ:",
    },
}

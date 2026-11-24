# 🏈 GridironMetrics-CFB

**GridironMetrics-CFB** is an end-to-end College Football analytics, scouting, and historical recap web application built with **Python**, **Streamlit**, **Pandas**, and the **College Football Data (CFBD) API**.

Spanning **17 FBS seasons (2010–2026)**, the platform transforms raw game, roster, and play-by-play telemetry into coaching-ready situational insights, side-by-side box score comparisons, positional game leaders, and multi-era championship recaps.

> 🔗 **Live App:** https://gridironmetrics.streamlit.app/

---

## ✨ Key Application Views

### 1. 🔍 Single Game Inspector
Drill down through **Conference ➔ Team ➔ Schedule** (covering regular season and postseason matchups from 2010–2026) to inspect any completed game:
* **Official Team Box Score Telemetry:** Side-by-side comparison of Total Yards, Passing Yards, Rushing Yards, First Downs, Turnovers, 3rd Down Conversions, and Completions/Attempts with automated green statistical-advantage highlighting.
* **Individual Statistical Leaders:** Identifies the top yardage performer for both teams in **Passing**, **Rushing**, and **Receiving**, automatically mapped to official season rosters to display player positions (`QB`, `RB`, `WR`, `TE`) alongside full stat lines.
* **Chronological Game Play-by-Play Log:** Timestamped play-by-play breakdown sorted chronologically by Quarter, Game Clock, and Drive/Play sequence with running scores and color-coded row highlights for **Touchdowns**, **Field Goals**, and **Turnovers**.

### 2. 📊 Game Analysis Engine
Evaluates full-season conference performance benchmarks across any selected year (`2010–2026`), calculating average scoring margins, one-score game rates, and explosive game flags (`60+` combined points).

### 3. 🏈 Down & Distance Play Scouting Engine
A coaching-style situational film room allowing users to filter play-by-play telemetry by **Offensive Unit**, **Down (1st–4th)**, and **Impact Plays**:
* **Situational Success Rate:** Tracks whether each snap kept the offense on schedule:
  * **1st Down:** Gains ≥ 50% of yards needed.
  * **2nd Down:** Gains ≥ 70% of yards needed.
  * **3rd & 4th Down:** Gains ≥ 100% of yards needed for a first down.
* **Explosive Chunk Plays:** Flags passing gains of **15+ yards** and rushing gains of **10+ yards**.

### 4. 🏆 Season Recap (2010–2026)
A historical snapshot of every season across the BCS, 4-Team CFP, and 12-Team CFP eras:
* **National Championship Summary:** Displays the National Champion, Runner-Up, Title Game score, and National Championship **Offensive & Defensive MVPs**.
* **FBS Standings Extremes:** Dynamically computes season records from cached game results to highlight the top and bottom FBS records each year.
* **Conference Champions & Major Award Winners:** Lists every FBS conference champion alongside their final season record (`W–L`), paired with recipients for the **Heisman Trophy**, **Davey O'Brien**, **Doak Walker**, **Fred Biletnikoff**, **John Mackey**, **Dick Butkus**, **Jim Thorpe**, and **Lou Groza** awards.

---

## 🏗️ Project Architecture

```text
gridironmetrics-cfb/
├── app.py              # Main Streamlit dashboard, navigation sidebar, and UI renderers
├── ingest.py           # CFBD SDK data ingestion & local/cloud JSON caching layer
├── analytics.py        # Box score parsing, roster position mapping, and play-by-play metrics
├── season_recap.py     # 2010–2026 championship metadata, dynamic standings, and award tables
├── requirements.txt    # Python dependencies (streamlit, cfbd, pandas, python-dotenv)
└── data/               # Auto-generated JSON cache to minimize API calls and speed up loads

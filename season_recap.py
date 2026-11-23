import os
import json
import pandas as pd
import streamlit as st
from ingest import get_secret, fetch_and_cache_games

CHAMPIONSHIP_DATA = {
    2026: {
        "national_champion": "TBD (Season in Progress)",
        "runner_up": "TBD (Season in Progress)",
        "title_score": "—",
        "conference_champions": {
            "SEC": "TBD",
            "Big Ten": "TBD",
            "ACC": "TBD",
            "Big 12": "TBD",
            "American": "TBD",
            "Mountain West": "TBD",
            "Sun Belt": "TBD",
            "MAC": "TBD",
            "CUSA": "TBD",
            "Pac-12": "TBD",
        },
    },
    2025: {
        "national_champion": "Indiana Hoosiers (16–0)",
        "runner_up": "Miami Hurricanes (13–2)",
        "title_score": "27–21",
        "conference_champions": {
            "Big Ten": "Indiana",
            "SEC": "Georgia",
            "ACC": "Duke",
            "Big 12": "Texas Tech",
            "Sun Belt": "James Madison",
            "American": "Tulane",
            "Mountain West": "Boise State",
            "MAC": "Western Michigan",
            "CUSA": "Kennesaw State",
        },
    },
    2024: {
        "national_champion": "Ohio State Buckeyes (14–2)",
        "runner_up": "Notre Dame Fighting Irish (14–2)",
        "title_score": "34–23",
        "conference_champions": {
            "Big Ten": "Oregon",
            "SEC": "Georgia",
            "ACC": "Clemson",
            "Big 12": "Arizona State",
            "Mountain West": "Boise State",
            "American": "Army",
            "Sun Belt": "Marshall",
            "MAC": "Ohio",
            "CUSA": "Jacksonville State",
        },
    },
    2023: {
        "national_champion": "Michigan Wolverines (15–0)",
        "runner_up": "Washington Huskies (14–1)",
        "title_score": "34–13",
        "conference_champions": {
            "Big Ten": "Michigan",
            "SEC": "Alabama",
            "ACC": "Florida State",
            "Big 12": "Texas",
            "Pac-12": "Washington",
            "Mountain West": "Boise State",
            "American": "SMU",
            "Sun Belt": "Troy",
            "MAC": "Miami (OH)",
            "CUSA": "Liberty",
        },
    },
    2022: {
        "national_champion": "Georgia Bulldogs (15–0)",
        "runner_up": "TCU Horned Frogs (13–2)",
        "title_score": "65–7",
        "conference_champions": {
            "SEC": "Georgia",
            "Big Ten": "Michigan",
            "ACC": "Clemson",
            "Big 12": "Kansas State",
            "Pac-12": "Utah",
            "American": "Tulane",
            "Mountain West": "Fresno State",
            "Sun Belt": "Troy",
            "MAC": "Toledo",
            "CUSA": "UTSA",
        },
    },
    2021: {
        "national_champion": "Georgia Bulldogs (14–1)",
        "runner_up": "Alabama Crimson Tide (13–2)",
        "title_score": "33–18",
        "conference_champions": {
            "SEC": "Alabama",
            "Big Ten": "Michigan",
            "ACC": "Pittsburgh",
            "Big 12": "Baylor",
            "Pac-12": "Utah",
            "American": "Cincinnati",
            "Mountain West": "Utah State",
            "Sun Belt": "Louisiana",
            "MAC": "Northern Illinois",
            "CUSA": "UTSA",
        },
    },
    2020: {
        "national_champion": "Alabama Crimson Tide (13–0)",
        "runner_up": "Ohio State Buckeyes (7–1)",
        "title_score": "52–24",
        "conference_champions": {
            "SEC": "Alabama",
            "Big Ten": "Ohio State",
            "ACC": "Clemson",
            "Big 12": "Oklahoma",
            "Pac-12": "Oregon",
            "American": "Cincinnati",
            "Mountain West": "San Jose State",
            "Sun Belt": "Coastal Carolina & Louisiana",
            "MAC": "Ball State",
            "CUSA": "UAB",
        },
    },
    2019: {
        "national_champion": "LSU Tigers (15–0)",
        "runner_up": "Clemson Tigers (14–1)",
        "title_score": "42–25",
        "conference_champions": {
            "SEC": "LSU",
            "Big Ten": "Ohio State",
            "ACC": "Clemson",
            "Big 12": "Oklahoma",
            "Pac-12": "Oregon",
            "American": "Memphis",
            "Mountain West": "Boise State",
            "Sun Belt": "Appalachian State",
            "MAC": "Miami (OH)",
            "CUSA": "Florida Atlantic",
        },
    },
    2018: {
        "national_champion": "Clemson Tigers (15–0)",
        "runner_up": "Alabama Crimson Tide (14–1)",
        "title_score": "44–16",
        "conference_champions": {
            "ACC": "Clemson",
            "SEC": "Alabama",
            "Big Ten": "Ohio State",
            "Big 12": "Oklahoma",
            "Pac-12": "Washington",
            "American": "UCF",
            "Mountain West": "Fresno State",
            "Sun Belt": "Appalachian State",
            "MAC": "Northern Illinois",
            "CUSA": "UAB",
        },
    },
    2017: {
        "national_champion": "Alabama Crimson Tide (13–1)",
        "runner_up": "Georgia Bulldogs (13–2)",
        "title_score": "26–23 (OT)",
        "conference_champions": {
            "SEC": "Georgia",
            "Big Ten": "Ohio State",
            "ACC": "Clemson",
            "Big 12": "Oklahoma",
            "Pac-12": "USC",
            "American": "UCF",
            "Mountain West": "Boise State",
            "Sun Belt": "Appalachian State & Troy",
            "MAC": "Toledo",
            "CUSA": "Florida Atlantic",
        },
    },
    2016: {
        "national_champion": "Clemson Tigers (14–1)",
        "runner_up": "Alabama Crimson Tide (14–1)",
        "title_score": "35–31",
        "conference_champions": {
            "ACC": "Clemson",
            "SEC": "Alabama",
            "Big Ten": "Penn State",
            "Big 12": "Oklahoma",
            "Pac-12": "Washington",
            "American": "Temple",
            "Mountain West": "San Diego State",
            "Sun Belt": "Appalachian State & Arkansas State",
            "MAC": "Western Michigan",
            "CUSA": "Western Kentucky",
        },
    },
    2015: {
        "national_champion": "Alabama Crimson Tide (14–1)",
        "runner_up": "Clemson Tigers (14–1)",
        "title_score": "45–40",
        "conference_champions": {
            "SEC": "Alabama",
            "ACC": "Clemson",
            "Big Ten": "Michigan State",
            "Big 12": "Oklahoma",
            "Pac-12": "Stanford",
            "American": "Houston",
            "Mountain West": "San Diego State",
            "Sun Belt": "Arkansas State",
            "MAC": "Bowling Green",
            "CUSA": "Western Kentucky",
        },
    },
    2014: {
        "national_champion": "Ohio State Buckeyes (14–1)",
        "runner_up": "Oregon Ducks (13–2)",
        "title_score": "42–20",
        "conference_champions": {
            "Big Ten": "Ohio State",
            "Pac-12": "Oregon",
            "SEC": "Alabama",
            "ACC": "Florida State",
            "Big 12": "Baylor & TCU",
            "American": "Cincinnati & Memphis & UCF",
            "Mountain West": "Boise State",
            "Sun Belt": "Georgia Southern",
            "MAC": "Northern Illinois",
            "CUSA": "Marshall",
        },
    },
    2013: {
        "national_champion": "Florida State Seminoles (14–0)",
        "runner_up": "Auburn Tigers (12–2)",
        "title_score": "34–31 (BCS)",
        "conference_champions": {
            "ACC": "Florida State",
            "SEC": "Auburn",
            "Big Ten": "Michigan State",
            "Big 12": "Baylor",
            "Pac-12": "Stanford",
            "American": "UCF",
            "Mountain West": "Fresno State",
            "Sun Belt": "Arkansas State & Louisiana",
            "MAC": "Bowling Green",
            "CUSA": "Rice",
        },
    },
    2012: {
        "national_champion": "Alabama Crimson Tide (13–1)",
        "runner_up": "Notre Dame Fighting Irish (12–1)",
        "title_score": "42–14 (BCS)",
        "conference_champions": {
            "SEC": "Alabama",
            "Big Ten": "Wisconsin",
            "ACC": "Florida State",
            "Big 12": "Kansas State & Oklahoma",
            "Pac-12": "Stanford",
            "Big East": "Cincinnati & Louisville & Rutgers & Syracuse",
            "Mountain West": "Boise State & Fresno State & San Diego State",
            "Sun Belt": "Arkansas State",
            "MAC": "Northern Illinois",
            "CUSA": "Tulsa",
            "WAC": "Utah State",
        },
    },
    2011: {
        "national_champion": "Alabama Crimson Tide (12–1)",
        "runner_up": "LSU Tigers (13–1)",
        "title_score": "21–0 (BCS)",
        "conference_champions": {
            "SEC": "LSU",
            "Big Ten": "Wisconsin",
            "ACC": "Clemson",
            "Big 12": "Oklahoma State",
            "Pac-12": "Oregon",
            "Big East": "Cincinnati & Louisville & West Virginia",
            "Mountain West": "TCU",
            "Sun Belt": "Arkansas State",
            "MAC": "Northern Illinois",
            "CUSA": "Southern Miss",
            "WAC": "Louisiana Tech",
        },
    },
    2010: {
        "national_champion": "Auburn Tigers (14–0)",
        "runner_up": "Oregon Ducks (12–1)",
        "title_score": "22–19 (BCS)",
        "conference_champions": {
            "SEC": "Auburn",
            "Pac-10": "Oregon",
            "Big Ten": "Michigan State & Ohio State & Wisconsin",
            "ACC": "Virginia Tech",
            "Big 12": "Oklahoma",
            "Big East": "Connecticut & Pittsburgh & West Virginia",
            "Mountain West": "TCU",
            "Sun Belt": "FIU & Troy",
            "MAC": "Miami (OH)",
            "CUSA": "UCF",
            "WAC": "Boise State & Hawaii & Nevada",
        },
    },
}


@st.cache_data(ttl=3600)
def fetch_season_records_df(year: int) -> pd.DataFrame:
    """Computes FBS team season records directly from cached game results (records_{year}.json)."""
    output_dir = get_secret("OUTPUT_DIR", "./data")
    filepath = os.path.join(output_dir, f"records_{year}.json")

    if not os.path.exists(filepath):
        fetch_and_cache_games(year=int(year))

    if not os.path.exists(filepath):
        return pd.DataFrame()

    with open(filepath, "r", encoding="utf-8") as f:
        games_list = json.load(f)

    if not games_list:
        return pd.DataFrame()

    df = pd.DataFrame(games_list)
    cols = df.columns.tolist()

    home_team_key = next((c for c in cols if "home_team" in c.lower() or "hometeam" in c.lower()), "home_team")
    away_team_key = next((c for c in cols if "away_team" in c.lower() or "awayteam" in c.lower()), "away_team")
    home_pts_key = next((c for c in cols if "home_points" in c.lower() or "homepoints" in c.lower()), "home_points")
    away_pts_key = next((c for c in cols if "away_points" in c.lower() or "awaypoints" in c.lower()), "away_points")
    home_conf_key = next((c for c in cols if "conference" in c.lower() and "home" in c.lower()), None)
    away_conf_key = next((c for c in cols if "conference" in c.lower() and "away" in c.lower()), None)
    home_class_key = next((c for c in cols if "classification" in c.lower() and "home" in c.lower()), None)
    away_class_key = next((c for c in cols if "classification" in c.lower() and "away" in c.lower()), None)

    df["h_pts"] = pd.to_numeric(df[home_pts_key], errors="coerce")
    df["a_pts"] = pd.to_numeric(df[away_pts_key], errors="coerce")
    completed = df.dropna(subset=["h_pts", "a_pts"]).copy()

    standings = {}

    def _ensure_team(team, conf, classification):
        if not team or (classification and str(classification).lower() != "fbs"):
            return False
        if team not in standings:
            standings[team] = {
                "Team": team,
                "Conference": conf if conf and str(conf) != "None" else "Independent",
                "Wins": 0,
                "Losses": 0,
            }
        return True

    for _, row in completed.iterrows():
        ht = row.get(home_team_key)
        at = row.get(away_team_key)
        hc = row.get(home_conf_key) if home_conf_key else None
        ac = row.get(away_conf_key) if away_conf_key else None
        h_cls = row.get(home_class_key) if home_class_key else "fbs"
        a_cls = row.get(away_class_key) if away_class_key else "fbs"

        hp = int(row["h_pts"])
        ap = int(row["a_pts"])

        h_ok = _ensure_team(ht, hc, h_cls)
        a_ok = _ensure_team(at, ac, a_cls)

        if hp > ap:
            if h_ok:
                standings[ht]["Wins"] += 1
            if a_ok:
                standings[at]["Losses"] += 1
        elif ap > hp:
            if a_ok:
                standings[at]["Wins"] += 1
            if h_ok:
                standings[ht]["Losses"] += 1

    rows = []
    for team_data in standings.values():
        w = team_data["Wins"]
        l = team_data["Losses"]
        total_games = w + l
        win_pct = (w / total_games) if total_games > 0 else 0.0
        rows.append({
            "Team": team_data["Team"],
            "Conference": team_data["Conference"],
            "Wins": w,
            "Losses": l,
            "Record": f"{w}–{l}",
            "Win %": round(win_pct, 3),
        })

    return pd.DataFrame(rows)


def _format_champion_with_record(champ_entry: str, record_lookup: dict) -> str:
    """Appends each team's season record next to its name (handles '&' co-champions too)."""
    if not champ_entry or champ_entry.startswith("TBD") or not record_lookup:
        return champ_entry

    if " & " in champ_entry:
        parts = [p.strip() for p in champ_entry.split("&")]
        formatted_parts = [
            f"{p} ({record_lookup[p]})" if p in record_lookup else p
            for p in parts
        ]
        return " & ".join(formatted_parts)

    if champ_entry in record_lookup:
        return f"{champ_entry} ({record_lookup[champ_entry]})"
    return champ_entry


def _render_champ_card(label: str, team_text: str, badge_text: str = None):
    """Renders a compact championship card with small, clean typography that fits at 100% zoom."""
    badge_html = (
        f"<div style='margin-top:5px;'>"
        f"<span style='display:inline-block; padding:2px 8px; border-radius:999px; "
        f"background-color:rgba(16, 185, 129, 0.2); color:#6ee7b7; font-size:0.75rem; font-weight:600;'>"
        f"{badge_text}</span></div>"
        if badge_text else ""
    )
    st.markdown(
        f"""
        <div style="padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.12); background-color: rgba(255,255,255,0.03);">
            <div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 3px;">{label}</div>
            <div style="font-size: 0.98rem; font-weight: 700; line-height: 1.25;">{team_text}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_season_recap(selected_year: int):
    st.title(f"🏆 {selected_year} CFB Season Recap")
    st.markdown(f"Championship results, top and bottom FBS records, and conference title winners for the **{selected_year}** season.")

    meta = CHAMPIONSHIP_DATA.get(selected_year, {})

    # --- COMPACT NATIONAL CHAMPION & RUNNER-UP CARDS ---
    col1, col2 = st.columns(2)
    with col1:
        score = meta.get("title_score")
        _render_champ_card(
            label="🥇 National Champion",
            team_text=meta.get("national_champion", "N/A"),
            badge_text=f"Title Game: {score}" if score and score != "—" else None,
        )
    with col2:
        _render_champ_card(
            label="🥈 National Runner-Up",
            team_text=meta.get("runner_up", "N/A"),
        )

    st.divider()

    # --- BEST & WORST RECORD TEAMS ---
    record_lookup = {}
    with st.spinner(f"Calculating {selected_year} FBS team records..."):
        try:
            df_records = fetch_season_records_df(selected_year)
        except Exception as e:
            st.error(f"Could not load season records: {e}")
            df_records = pd.DataFrame()

    if not df_records.empty:
        record_lookup = dict(zip(df_records["Team"], df_records["Record"]))
        active_df = df_records[(df_records["Wins"] + df_records["Losses"]) > 0].copy()
        if not active_df.empty:
            best_df = active_df.sort_values(by=["Win %", "Wins"], ascending=[False, False])
            worst_df = active_df.sort_values(by=["Win %", "Losses"], ascending=[True, False])

            top_pct = best_df.iloc[0]["Win %"]
            best_teams = best_df[best_df["Win %"] == top_pct]

            bottom_pct = worst_df.iloc[0]["Win %"]
            worst_teams = worst_df[worst_df["Win %"] == bottom_pct]

            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.subheader("📈 Best Record Team(s)")
                for _, row in best_teams.iterrows():
                    st.success(f"**{row['Team']}** ({row['Conference']}) — **{row['Record']}** ({row['Win %']:.3f})")

            with r_col2:
                st.subheader("📉 Worst Record Team(s)")
                for _, row in worst_teams.iterrows():
                    st.error(f"**{row['Team']}** ({row['Conference']}) — **{row['Record']}** ({row['Win %']:.3f})")

    st.divider()

    # --- CONFERENCE CHAMPIONS (WITH RECORDS) ---
    st.subheader("🏅 Conference Champions")
    conf_champs = meta.get("conference_champions", {})
    if conf_champs:
        formatted_rows = [
            {
                "Conference": conf,
                "Champion": _format_champion_with_record(champ, record_lookup),
            }
            for conf, champ in conf_champs.items()
        ]
        conf_df = pd.DataFrame(formatted_rows)
        st.dataframe(conf_df, width="stretch", hide_index=True)
    else:
        st.info(f"Conference championship data not yet configured for {selected_year}.")
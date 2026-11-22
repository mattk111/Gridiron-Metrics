import os
import json
import pandas as pd
import streamlit as st
from ingest import get_games_api, get_secret

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
}


@st.cache_data(ttl=3600)
def fetch_season_records_df(year: int) -> pd.DataFrame:
    """Fetches FBS team season records via cfbd GamesApi and caches locally."""
    output_dir = get_secret("OUTPUT_DIR", "./data")
    os.makedirs(output_dir, exist_ok=True)
    cache_path = os.path.join(output_dir, f"team_records_{year}.json")

    if os.path.exists(cache_path) and year != 2026:
        with open(cache_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
    else:
        games_api = get_games_api()
        records_data = games_api.get_team_records(year=int(year))
        raw_list = [r.to_dict() for r in records_data]
        if raw_list:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(raw_list, f, default=str, indent=4)

    rows = []
    for rec in raw_list:
        classification = str(rec.get("classification") or "").lower()
        if classification and classification != "fbs":
            continue
        total = rec.get("total") or {}
        wins = int(total.get("wins") or 0)
        losses = int(total.get("losses") or 0)
        games = wins + losses
        win_pct = (wins / games) if games > 0 else 0.0
        rows.append({
            "Team": rec.get("team"),
            "Conference": rec.get("conference") or "Independent",
            "Wins": wins,
            "Losses": losses,
            "Record": f"{wins}-{losses}",
            "Win %": round(win_pct, 3),
        })
    return pd.DataFrame(rows)


def render_season_recap(selected_year: int):
    st.title(f"🏆 {selected_year} CFB Season Recap")
    st.markdown(f"Championship results, top and bottom FBS records, and conference title winners for the **{selected_year}** season.")

    meta = CHAMPIONSHIP_DATA.get(selected_year, {})

    # --- NATIONAL CHAMPION & RUNNER-UP ---
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="🥇 National Champion",
            value=meta.get("national_champion", "N/A"),
            delta=f"Title Game: {meta.get('title_score')}" if meta.get("title_score") and meta.get("title_score") != "—" else None,
        )
    with col2:
        st.metric(
            label="🥈 National Runner-Up",
            value=meta.get("runner_up", "N/A"),
        )

    st.divider()

    # --- BEST & WORST RECORD TEAMS ---
    with st.spinner(f"Loading {selected_year} FBS team records..."):
        try:
            df_records = fetch_season_records_df(selected_year)
        except Exception as e:
            st.error(f"Could not load season records: {e}")
            df_records = pd.DataFrame()

    if not df_records.empty:
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

    # --- CONFERENCE CHAMPIONS ---
    st.subheader("🏅 Conference Champions")
    conf_champs = meta.get("conference_champions", {})
    if conf_champs:
        conf_df = pd.DataFrame(list(conf_champs.items()), columns=["Conference", "Champion"])
        st.dataframe(conf_df, width="stretch", hide_index=True)
    else:
        st.info(f"Conference championship data not yet configured for {selected_year}.")
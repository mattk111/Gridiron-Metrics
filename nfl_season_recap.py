import pandas as pd
import streamlit as st
from nfl_ingest import fetch_nfl_schedules
from nfl_analytics import NFL_DIVISIONS, NFL_TEAM_NAMES, normalize_nfl_abbr

NFL_AWARD_INFO = [
    ("AP Most Valuable Player", "(League MVP)"),
    ("AP Offensive Player of the Year", "(Top Offensive Player)"),
    ("AP Defensive Player of the Year", "(Top Defensive Player)"),
    ("AP Offensive Rookie of the Year", "(Top 1st-Year Offensive Player)"),
    ("AP Defensive Rookie of the Year", "(Top 1st-Year Defensive Player)"),
    ("AP Comeback Player of the Year", "(Top Comeback Season)"),
    ("AP Coach of the Year", "(Top Head Coach)"),
]

NFL_CHAMPIONSHIP_DATA = {
    2026: {
        "super_bowl": "Super Bowl LXI",
        "champion": "TBD (Season in Progress)",
        "runner_up": "TBD (Season in Progress)",
        "title_score": "—",
        "sb_mvp": "TBD (Feb 2027)",
        "division_champions": {div: "TBD" for div in NFL_DIVISIONS},
        "awards": {name: "TBD (Feb 2027)" for name, _ in NFL_AWARD_INFO},
    },
    2025: {
        "super_bowl": "Super Bowl LX",
        "champion": "Seattle Seahawks (14–3)",
        "runner_up": "New England Patriots (14–3)",
        "title_score": "29–13",
        "sb_mvp": "Kenneth Walker III (RB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "PIT",
            "AFC South": "JAX",
            "AFC West": "DEN",
            "NFC East": "PHI",
            "NFC North": "CHI",
            "NFC South": "CAR",
            "NFC West": "SEA",
        },
        "awards": {
            "AP Most Valuable Player": "Matthew Stafford, Los Angeles Rams",
            "AP Offensive Player of the Year": "Jaxon Smith-Njigba, Seattle Seahawks",
            "AP Defensive Player of the Year": "Myles Garrett, Cleveland Browns",
            "AP Offensive Rookie of the Year": "Tetairoa McMillan, Carolina Panthers",
            "AP Defensive Rookie of the Year": "Carson Schwesinger, Cleveland Browns",
            "AP Comeback Player of the Year": "Christian McCaffrey, San Francisco 49ers",
            "AP Coach of the Year": "Mike Vrabel, New England Patriots",
        },
    },
    2024: {
        "super_bowl": "Super Bowl LIX",
        "champion": "Philadelphia Eagles (14–3)",
        "runner_up": "Kansas City Chiefs (15–2)",
        "title_score": "40–22",
        "sb_mvp": "Jalen Hurts (QB)",
        "division_champions": {
            "AFC East": "BUF",
            "AFC North": "BAL",
            "AFC South": "HOU",
            "AFC West": "KC",
            "NFC East": "PHI",
            "NFC North": "DET",
            "NFC South": "TB",
            "NFC West": "LA",
        },
        "awards": {
            "AP Most Valuable Player": "Josh Allen, Buffalo Bills",
            "AP Offensive Player of the Year": "Saquon Barkley, Philadelphia Eagles",
            "AP Defensive Player of the Year": "Patrick Surtain II, Denver Broncos",
            "AP Offensive Rookie of the Year": "Jayden Daniels, Washington Commanders",
            "AP Defensive Rookie of the Year": "Jared Verse, Los Angeles Rams",
            "AP Comeback Player of the Year": "Joe Burrow, Cincinnati Bengals",
            "AP Coach of the Year": "Kevin O'Connell, Minnesota Vikings",
        },
    },
    2023: {
        "super_bowl": "Super Bowl LVIII",
        "champion": "Kansas City Chiefs (11–6)",
        "runner_up": "San Francisco 49ers (12–5)",
        "title_score": "25–22 (OT)",
        "sb_mvp": "Patrick Mahomes (QB)",
        "division_champions": {
            "AFC East": "BUF",
            "AFC North": "BAL",
            "AFC South": "HOU",
            "AFC West": "KC",
            "NFC East": "DAL",
            "NFC North": "DET",
            "NFC South": "TB",
            "NFC West": "SF",
        },
        "awards": {
            "AP Most Valuable Player": "Lamar Jackson, Baltimore Ravens",
            "AP Offensive Player of the Year": "Christian McCaffrey, San Francisco 49ers",
            "AP Defensive Player of the Year": "Myles Garrett, Cleveland Browns",
            "AP Offensive Rookie of the Year": "C.J. Stroud, Houston Texans",
            "AP Defensive Rookie of the Year": "Will Anderson Jr., Houston Texans",
            "AP Comeback Player of the Year": "Joe Flacco, Cleveland Browns",
            "AP Coach of the Year": "Kevin Stefanski, Cleveland Browns",
        },
    },
    2022: {
        "super_bowl": "Super Bowl LVII",
        "champion": "Kansas City Chiefs (14–3)",
        "runner_up": "Philadelphia Eagles (14–3)",
        "title_score": "38–35",
        "sb_mvp": "Patrick Mahomes (QB)",
        "division_champions": {
            "AFC East": "BUF",
            "AFC North": "CIN",
            "AFC South": "JAX",
            "AFC West": "KC",
            "NFC East": "PHI",
            "NFC North": "MIN",
            "NFC South": "TB",
            "NFC West": "SF",
        },
        "awards": {
            "AP Most Valuable Player": "Patrick Mahomes, Kansas City Chiefs",
            "AP Offensive Player of the Year": "Justin Jefferson, Minnesota Vikings",
            "AP Defensive Player of the Year": "Nick Bosa, San Francisco 49ers",
            "AP Offensive Rookie of the Year": "Garrett Wilson, New York Jets",
            "AP Defensive Rookie of the Year": "Sauce Gardner, New York Jets",
            "AP Comeback Player of the Year": "Geno Smith, Seattle Seahawks",
            "AP Coach of the Year": "Brian Daboll, New York Giants",
        },
    },
    2021: {
        "super_bowl": "Super Bowl LVI",
        "champion": "Los Angeles Rams (12–5)",
        "runner_up": "Cincinnati Bengals (10–7)",
        "title_score": "23–20",
        "sb_mvp": "Cooper Kupp (WR)",
        "division_champions": {
            "AFC East": "BUF",
            "AFC North": "CIN",
            "AFC South": "TEN",
            "AFC West": "KC",
            "NFC East": "DAL",
            "NFC North": "GB",
            "NFC South": "TB",
            "NFC West": "LA",
        },
        "awards": {
            "AP Most Valuable Player": "Aaron Rodgers, Green Bay Packers",
            "AP Offensive Player of the Year": "Cooper Kupp, Los Angeles Rams",
            "AP Defensive Player of the Year": "T.J. Watt, Pittsburgh Steelers",
            "AP Offensive Rookie of the Year": "Ja'Marr Chase, Cincinnati Bengals",
            "AP Defensive Rookie of the Year": "Micah Parsons, Dallas Cowboys",
            "AP Comeback Player of the Year": "Joe Burrow, Cincinnati Bengals",
            "AP Coach of the Year": "Mike Vrabel, Tennessee Titans",
        },
    },
    2020: {
        "super_bowl": "Super Bowl LV",
        "champion": "Tampa Bay Buccaneers (11–5)",
        "runner_up": "Kansas City Chiefs (14–2)",
        "title_score": "31–9",
        "sb_mvp": "Tom Brady (QB)",
        "division_champions": {
            "AFC East": "BUF",
            "AFC North": "PIT",
            "AFC South": "TEN",
            "AFC West": "KC",
            "NFC East": "WAS",
            "NFC North": "GB",
            "NFC South": "NO",
            "NFC West": "SEA",
        },
        "awards": {
            "AP Most Valuable Player": "Aaron Rodgers, Green Bay Packers",
            "AP Offensive Player of the Year": "Derrick Henry, Tennessee Titans",
            "AP Defensive Player of the Year": "Aaron Donald, Los Angeles Rams",
            "AP Offensive Rookie of the Year": "Justin Herbert, Los Angeles Chargers",
            "AP Defensive Rookie of the Year": "Chase Young, Washington Football Team",
            "AP Comeback Player of the Year": "Alex Smith, Washington Football Team",
            "AP Coach of the Year": "Kevin Stefanski, Cleveland Browns",
        },
    },
    2019: {
        "super_bowl": "Super Bowl LIV",
        "champion": "Kansas City Chiefs (12–4)",
        "runner_up": "San Francisco 49ers (13–3)",
        "title_score": "31–20",
        "sb_mvp": "Patrick Mahomes (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "BAL",
            "AFC South": "HOU",
            "AFC West": "KC",
            "NFC East": "PHI",
            "NFC North": "GB",
            "NFC South": "NO",
            "NFC West": "SF",
        },
        "awards": {
            "AP Most Valuable Player": "Lamar Jackson, Baltimore Ravens",
            "AP Offensive Player of the Year": "Michael Thomas, New Orleans Saints",
            "AP Defensive Player of the Year": "Stephon Gilmore, New England Patriots",
            "AP Offensive Rookie of the Year": "Kyler Murray, Arizona Cardinals",
            "AP Defensive Rookie of the Year": "Nick Bosa, San Francisco 49ers",
            "AP Comeback Player of the Year": "Ryan Tannehill, Tennessee Titans",
            "AP Coach of the Year": "John Harbaugh, Baltimore Ravens",
        },
    },
    2018: {
        "super_bowl": "Super Bowl LIII",
        "champion": "New England Patriots (11–5)",
        "runner_up": "Los Angeles Rams (13–3)",
        "title_score": "13–3",
        "sb_mvp": "Julian Edelman (WR)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "BAL",
            "AFC South": "HOU",
            "AFC West": "KC",
            "NFC East": "DAL",
            "NFC North": "CHI",
            "NFC South": "NO",
            "NFC West": "LA",
        },
        "awards": {
            "AP Most Valuable Player": "Patrick Mahomes, Kansas City Chiefs",
            "AP Offensive Player of the Year": "Patrick Mahomes, Kansas City Chiefs",
            "AP Defensive Player of the Year": "Aaron Donald, Los Angeles Rams",
            "AP Offensive Rookie of the Year": "Saquon Barkley, New York Giants",
            "AP Defensive Rookie of the Year": "Darius Leonard, Indianapolis Colts",
            "AP Comeback Player of the Year": "Andrew Luck, Indianapolis Colts",
            "AP Coach of the Year": "Matt Nagy, Chicago Bears",
        },
    },
    2017: {
        "super_bowl": "Super Bowl LII",
        "champion": "Philadelphia Eagles (13–3)",
        "runner_up": "New England Patriots (13–3)",
        "title_score": "41–33",
        "sb_mvp": "Nick Foles (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "PIT",
            "AFC South": "JAX",
            "AFC West": "KC",
            "NFC East": "PHI",
            "NFC North": "MIN",
            "NFC South": "NO",
            "NFC West": "LA",
        },
        "awards": {
            "AP Most Valuable Player": "Tom Brady, New England Patriots",
            "AP Offensive Player of the Year": "Todd Gurley, Los Angeles Rams",
            "AP Defensive Player of the Year": "Aaron Donald, Los Angeles Rams",
            "AP Offensive Rookie of the Year": "Alvin Kamara, New Orleans Saints",
            "AP Defensive Rookie of the Year": "Marshon Lattimore, New Orleans Saints",
            "AP Comeback Player of the Year": "Keenan Allen, Los Angeles Chargers",
            "AP Coach of the Year": "Sean McVay, Los Angeles Rams",
        },
    },
    2016: {
        "super_bowl": "Super Bowl LI",
        "champion": "New England Patriots (14–2)",
        "runner_up": "Atlanta Falcons (11–5)",
        "title_score": "34–28 (OT)",
        "sb_mvp": "Tom Brady (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "PIT",
            "AFC South": "HOU",
            "AFC West": "KC",
            "NFC East": "DAL",
            "NFC North": "GB",
            "NFC South": "ATL",
            "NFC West": "SEA",
        },
        "awards": {
            "AP Most Valuable Player": "Matt Ryan, Atlanta Falcons",
            "AP Offensive Player of the Year": "Matt Ryan, Atlanta Falcons",
            "AP Defensive Player of the Year": "Khalil Mack, Oakland Raiders",
            "AP Offensive Rookie of the Year": "Dak Prescott, Dallas Cowboys",
            "AP Defensive Rookie of the Year": "Joey Bosa, San Diego Chargers",
            "AP Comeback Player of the Year": "Jordy Nelson, Green Bay Packers",
            "AP Coach of the Year": "Jason Garrett, Dallas Cowboys",
        },
    },
    2015: {
        "super_bowl": "Super Bowl 50",
        "champion": "Denver Broncos (12–4)",
        "runner_up": "Carolina Panthers (15–1)",
        "title_score": "24–10",
        "sb_mvp": "Von Miller (LB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "CIN",
            "AFC South": "HOU",
            "AFC West": "DEN",
            "NFC East": "WAS",
            "NFC North": "MIN",
            "NFC South": "CAR",
            "NFC West": "ARI",
        },
        "awards": {
            "AP Most Valuable Player": "Cam Newton, Carolina Panthers",
            "AP Offensive Player of the Year": "Cam Newton, Carolina Panthers",
            "AP Defensive Player of the Year": "J.J. Watt, Houston Texans",
            "AP Offensive Rookie of the Year": "Todd Gurley, St. Louis Rams",
            "AP Defensive Rookie of the Year": "Marcus Peters, Kansas City Chiefs",
            "AP Comeback Player of the Year": "Eric Berry, Kansas City Chiefs",
            "AP Coach of the Year": "Ron Rivera, Carolina Panthers",
        },
    },
    2014: {
        "super_bowl": "Super Bowl XLIX",
        "champion": "New England Patriots (12–4)",
        "runner_up": "Seattle Seahawks (12–4)",
        "title_score": "28–24",
        "sb_mvp": "Tom Brady (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "PIT",
            "AFC South": "IND",
            "AFC West": "DEN",
            "NFC East": "DAL",
            "NFC North": "GB",
            "NFC South": "CAR",
            "NFC West": "SEA",
        },
        "awards": {
            "AP Most Valuable Player": "Aaron Rodgers, Green Bay Packers",
            "AP Offensive Player of the Year": "DeMarco Murray, Dallas Cowboys",
            "AP Defensive Player of the Year": "J.J. Watt, Houston Texans",
            "AP Offensive Rookie of the Year": "Odell Beckham Jr., New York Giants",
            "AP Defensive Rookie of the Year": "Aaron Donald, St. Louis Rams",
            "AP Comeback Player of the Year": "Rob Gronkowski, New England Patriots",
            "AP Coach of the Year": "Bruce Arians, Arizona Cardinals",
        },
    },
    2013: {
        "super_bowl": "Super Bowl XLVIII",
        "champion": "Seattle Seahawks (13–3)",
        "runner_up": "Denver Broncos (13–3)",
        "title_score": "43–8",
        "sb_mvp": "Malcolm Smith (LB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "CIN",
            "AFC South": "IND",
            "AFC West": "DEN",
            "NFC East": "PHI",
            "NFC North": "GB",
            "NFC South": "CAR",
            "NFC West": "SEA",
        },
        "awards": {
            "AP Most Valuable Player": "Peyton Manning, Denver Broncos",
            "AP Offensive Player of the Year": "Peyton Manning, Denver Broncos",
            "AP Defensive Player of the Year": "Luke Kuechly, Carolina Panthers",
            "AP Offensive Rookie of the Year": "Eddie Lacy, Green Bay Packers",
            "AP Defensive Rookie of the Year": "Sheldon Richardson, New York Jets",
            "AP Comeback Player of the Year": "Philip Rivers, San Diego Chargers",
            "AP Coach of the Year": "Ron Rivera, Carolina Panthers",
        },
    },
    2012: {
        "super_bowl": "Super Bowl XLVII",
        "champion": "Baltimore Ravens (10–6)",
        "runner_up": "San Francisco 49ers (11–4–1)",
        "title_score": "34–31",
        "sb_mvp": "Joe Flacco (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "BAL",
            "AFC South": "HOU",
            "AFC West": "DEN",
            "NFC East": "WAS",
            "NFC North": "GB",
            "NFC South": "ATL",
            "NFC West": "SF",
        },
        "awards": {
            "AP Most Valuable Player": "Adrian Peterson, Minnesota Vikings",
            "AP Offensive Player of the Year": "Adrian Peterson, Minnesota Vikings",
            "AP Defensive Player of the Year": "J.J. Watt, Houston Texans",
            "AP Offensive Rookie of the Year": "Robert Griffin III, Washington Redskins",
            "AP Defensive Rookie of the Year": "Luke Kuechly, Carolina Panthers",
            "AP Comeback Player of the Year": "Peyton Manning, Denver Broncos",
            "AP Coach of the Year": "Bruce Arians, Indianapolis Colts",
        },
    },
    2011: {
        "super_bowl": "Super Bowl XLVI",
        "champion": "New York Giants (9–7)",
        "runner_up": "New England Patriots (13–3)",
        "title_score": "21–17",
        "sb_mvp": "Eli Manning (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "BAL",
            "AFC South": "HOU",
            "AFC West": "DEN",
            "NFC East": "NYG",
            "NFC North": "GB",
            "NFC South": "NO",
            "NFC West": "SF",
        },
        "awards": {
            "AP Most Valuable Player": "Aaron Rodgers, Green Bay Packers",
            "AP Offensive Player of the Year": "Drew Brees, New Orleans Saints",
            "AP Defensive Player of the Year": "Terrell Suggs, Baltimore Ravens",
            "AP Offensive Rookie of the Year": "Cam Newton, Carolina Panthers",
            "AP Defensive Rookie of the Year": "Von Miller, Denver Broncos",
            "AP Comeback Player of the Year": "Matthew Stafford, Detroit Lions",
            "AP Coach of the Year": "Jim Harbaugh, San Francisco 49ers",
        },
    },
    2010: {
        "super_bowl": "Super Bowl XLV",
        "champion": "Green Bay Packers (10–6)",
        "runner_up": "Pittsburgh Steelers (12–4)",
        "title_score": "31–25",
        "sb_mvp": "Aaron Rodgers (QB)",
        "division_champions": {
            "AFC East": "NE",
            "AFC North": "PIT",
            "AFC South": "IND",
            "AFC West": "KC",
            "NFC East": "PHI",
            "NFC North": "CHI",
            "NFC South": "ATL",
            "NFC West": "SEA",
        },
        "awards": {
            "AP Most Valuable Player": "Tom Brady, New England Patriots",
            "AP Offensive Player of the Year": "Tom Brady, New England Patriots",
            "AP Defensive Player of the Year": "Troy Polamalu, Pittsburgh Steelers",
            "AP Offensive Rookie of the Year": "Sam Bradford, St. Louis Rams",
            "AP Defensive Rookie of the Year": "Ndamukong Suh, Detroit Lions",
            "AP Comeback Player of the Year": "Michael Vick, Philadelphia Eagles",
            "AP Coach of the Year": "Bill Belichick, New England Patriots",
        },
    },
}


@st.cache_data(ttl=3600)
def fetch_nfl_season_records_df(year: int) -> pd.DataFrame:
    """Computes regular-season NFL standings directly from nflverse schedule results."""
    df_sched = fetch_nfl_schedules(year=int(year))
    if df_sched.empty:
        return pd.DataFrame()

    reg = df_sched[df_sched["game_type"] == "REG"].copy() if "game_type" in df_sched.columns else df_sched.copy()
    reg["h_pts"] = pd.to_numeric(reg["home_score"], errors="coerce")
    reg["a_pts"] = pd.to_numeric(reg["away_score"], errors="coerce")
    completed = reg.dropna(subset=["h_pts", "a_pts"]).copy()

    div_lookup = {team: div for div, teams in NFL_DIVISIONS.items() for team in teams}
    standings = {}

    def _ensure(abbr):
        norm = normalize_nfl_abbr(abbr)
        if norm not in standings:
            standings[norm] = {
                "Abbr": norm,
                "Team": NFL_TEAM_NAMES.get(norm, norm),
                "Division": div_lookup.get(norm, "NFL"),
                "Wins": 0,
                "Losses": 0,
                "Ties": 0,
            }
        return norm

    for _, r in completed.iterrows():
        h = _ensure(r["home_team"])
        a = _ensure(r["away_team"])
        hp, ap = int(r["h_pts"]), int(r["a_pts"])

        if hp > ap:
            standings[h]["Wins"] += 1
            standings[a]["Losses"] += 1
        elif ap > hp:
            standings[a]["Wins"] += 1
            standings[h]["Losses"] += 1
        else:
            standings[h]["Ties"] += 1
            standings[a]["Ties"] += 1

    rows = []
    for d in standings.values():
        w, l, t = d["Wins"], d["Losses"], d["Ties"]
        games = w + l + t
        win_pct = ((w + 0.5 * t) / games) if games > 0 else 0.0
        rec_str = f"{w}–{l}–{t}" if t > 0 else f"{w}–{l}"
        rows.append({
            "Abbr": d["Abbr"],
            "Team": d["Team"],
            "Division": d["Division"],
            "Wins": w,
            "Losses": l,
            "Ties": t,
            "Record": rec_str,
            "Win %": round(win_pct, 3),
        })
    return pd.DataFrame(rows)


def _render_sb_card(label: str, team_text: str, badge_text: str = None, sb_mvp: str = None):
    badge_html = (
        f'<div style="margin-top:5px;">'
        f'<span style="display:inline-block; padding:2px 8px; border-radius:999px; '
        f'background-color:rgba(16, 185, 129, 0.2); color:#6ee7b7; font-size:0.75rem; font-weight:600;">'
        f'{badge_text}</span></div>'
        if badge_text else ""
    )
    mvp_html = (
        '<div style="margin-top:8px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.08); '
        'font-size:0.78rem; color:#d1d5db; line-height:1.4;">'
        f'<div><span style="color:#9ca3af;">Super Bowl MVP:</span> <strong>{sb_mvp}</strong></div>'
        '</div>'
        if sb_mvp else ""
    )
    card_html = (
        '<div style="padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.12); background-color: rgba(255,255,255,0.03);">'
        f'<div style="font-size: 0.78rem; color: #9ca3af; margin-bottom: 3px;">{label}</div>'
        f'<div style="font-size: 0.98rem; font-weight: 700; line-height: 1.25;">{team_text}</div>'
        f'{badge_html}'
        f'{mvp_html}'
        '</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def _render_nfl_awards_table(awards_dict: dict):
    rows_html = []
    for award_name, award_desc in NFL_AWARD_INFO:
        recipient = awards_dict.get(award_name, "N/A")
        rows_html.append(
            '<tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">'
            '<td style="padding: 9px 12px; vertical-align: middle; line-height: 1.3;">'
            f'<div style="font-weight: 600; font-size: 0.9rem; color: #f3f4f6;">{award_name}</div>'
            f'<div style="font-size: 0.78rem; color: #9ca3af;">{award_desc}</div>'
            '</td>'
            '<td style="padding: 9px 12px; vertical-align: middle; font-size: 0.9rem; color: #e5e7eb;">'
            f'{recipient}'
            '</td>'
            '</tr>'
        )
    table_html = (
        '<div style="border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; overflow: hidden;">'
        '<table style="width: 100%; border-collapse: collapse; background-color: rgba(255,255,255,0.02);">'
        '<thead>'
        '<tr style="background-color: rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.12); text-align: left;">'
        '<th style="padding: 10px 12px; font-size: 0.82rem; font-weight: 600; color: #9ca3af;">Award</th>'
        '<th style="padding: 10px 12px; font-size: 0.82rem; font-weight: 600; color: #9ca3af;">Recipient</th>'
        '</tr>'
        '</thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_nfl_season_recap(selected_year: int):
    meta = NFL_CHAMPIONSHIP_DATA.get(selected_year, {})
    sb_title = meta.get("super_bowl", "Super Bowl")
    st.title(f"🏆 {selected_year} NFL Season Recap ({sb_title})")
    st.markdown(f"Super Bowl results, top and bottom regular-season records, division champions, and AP award winners for the **{selected_year}** NFL season.")

    col1, col2 = st.columns(2)
    with col1:
        score = meta.get("title_score")
        _render_sb_card(
            label=f"🥇 {sb_title} Champion",
            team_text=meta.get("champion", "N/A"),
            badge_text=f"Final Score: {score}" if score and score != "—" else None,
            sb_mvp=meta.get("sb_mvp"),
        )
    with col2:
        _render_sb_card(
            label=f"🥈 {sb_title} Runner-Up",
            team_text=meta.get("runner_up", "N/A"),
        )

    st.divider()

    record_lookup = {}
    with st.spinner(f"Calculating {selected_year} NFL standings..."):
        try:
            df_records = fetch_nfl_season_records_df(selected_year)
        except Exception as e:
            st.error(f"Could not load NFL standings: {e}")
            df_records = pd.DataFrame()

    if not df_records.empty:
        record_lookup = dict(zip(df_records["Abbr"], df_records["Record"]))
        active_df = df_records[(df_records["Wins"] + df_records["Losses"] + df_records["Ties"]) > 0].copy()
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
                    st.success(f"**{row['Team']}** ({row['Division']}) — **{row['Record']}** ({row['Win %']:.3f})")

            with r_col2:
                st.subheader("📉 Worst Record Team(s)")
                for _, row in worst_teams.iterrows():
                    st.error(f"**{row['Team']}** ({row['Division']}) — **{row['Record']}** ({row['Win %']:.3f})")

    st.divider()

    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("🏅 Division Champions")
        div_champs = meta.get("division_champions", {})
        if div_champs:
            rows = []
            for div, abbr in div_champs.items():
                if abbr == "TBD":
                    champ_str = "TBD"
                else:
                    full_name = NFL_TEAM_NAMES.get(abbr, abbr)
                    rec = record_lookup.get(abbr)
                    champ_str = f"{full_name} ({rec})" if rec else full_name
                rows.append({"Division": div, "Champion": champ_str})
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    with right_col:
        st.subheader("🎖️ AP Award Winners")
        awards_dict = meta.get("awards", {})
        if awards_dict:
            _render_nfl_awards_table(awards_dict)
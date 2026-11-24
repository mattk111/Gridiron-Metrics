import pandas as pd
from nfl_ingest import (
    fetch_nfl_team_stats,
    fetch_nfl_player_stats,
    fetch_nfl_game_plays,
)

NFL_DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LA", "SEA", "SF"],
}

NFL_TEAM_NAMES = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "JAC": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams",
    "LAR": "Los Angeles Rams",
    "STL": "St. Louis Rams",
    "LAC": "Los Angeles Chargers",
    "SD": "San Diego Chargers",
    "LV": "Las Vegas Raiders",
    "OAK": "Oakland Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}


def normalize_nfl_abbr(abbr: str) -> str:
    """Normalizes legacy relocated franchise abbreviations (STL->LA, SD->LAC, OAK->LV, JAC->JAX)."""
    mapping = {"STL": "LA", "SD": "LAC", "OAK": "LV", "JAC": "JAX"}
    s = str(abbr or "").strip().upper()
    return mapping.get(s, s)


def get_nfl_team_label(abbr: str) -> str:
    norm = normalize_nfl_abbr(abbr)
    full = NFL_TEAM_NAMES.get(str(abbr).upper()) or NFL_TEAM_NAMES.get(norm, norm)
    return f"{full} ({norm})"


def get_nfl_teams_by_division(division: str) -> list:
    if division == "All NFL":
        all_codes = [t for teams in NFL_DIVISIONS.values() for t in teams]
        return sorted(all_codes)
    if division == "AFC":
        codes = [t for div, teams in NFL_DIVISIONS.items() if div.startswith("AFC") for t in teams]
        return sorted(codes)
    if division == "NFC":
        codes = [t for div, teams in NFL_DIVISIONS.items() if div.startswith("NFC") for t in teams]
        return sorted(codes)
    return sorted(NFL_DIVISIONS.get(division, []))


def get_nfl_team_schedule(df_sched: pd.DataFrame, team_abbr: str) -> pd.DataFrame:
    if df_sched.empty:
        return pd.DataFrame()
    df = df_sched.copy()
    df["home_norm"] = df["home_team"].apply(normalize_nfl_abbr)
    df["away_norm"] = df["away_team"].apply(normalize_nfl_abbr)
    target = normalize_nfl_abbr(team_abbr)
    sub = df[(df["home_norm"] == target) | (df["away_norm"] == target)].copy()
    if "week" in sub.columns:
        sub = sub.sort_values(by="week")
    return sub


def format_nfl_round(game_type: str, week: int) -> str:
    gt = str(game_type or "REG").upper()
    labels = {
        "REG": f"Week {week}",
        "WC": "Wild Card",
        "DIV": "Divisional",
        "CON": "Conf. Champ",
        "SB": "Super Bowl",
    }
    return labels.get(gt, f"Week {week}")


def _safe_int(val, default=0) -> int:
    num = pd.to_numeric(val, errors="coerce")
    return int(num) if pd.notna(num) else default


def parse_nfl_box_stats(game_id: str, week: int, away_abbr: str, home_abbr: str, year: int) -> dict:
    """Extracts official team box score stats for Away & Home teams in a given NFL game."""
    df_team = fetch_nfl_team_stats(year=year)
    if df_team.empty:
        return {}

    sub = df_team[df_team["week"] == int(week)].copy() if "week" in df_team.columns else df_team.copy()
    if "game_id" in sub.columns:
        g_sub = sub[sub["game_id"].astype(str) == str(game_id)]
        if not g_sub.empty:
            sub = g_sub

    parsed = {}
    for target_abbr in [away_abbr, home_abbr]:
        norm_t = normalize_nfl_abbr(target_abbr)
        t_rows = sub[sub["team"].apply(normalize_nfl_abbr) == norm_t]
        if t_rows.empty:
            continue
        r = t_rows.iloc[0]

        pass_yds = _safe_int(r.get("passing_yards", 0))
        rush_yds = _safe_int(r.get("rushing_yards", 0))
        total_yds = pass_yds + rush_yds

        pass_fd = _safe_int(r.get("passing_first_downs", 0))
        rush_fd = _safe_int(r.get("rushing_first_downs", 0))
        pen_fd = _safe_int(r.get("penalty_first_downs", 0))
        first_downs = pass_fd + rush_fd + pen_fd

        ints = _safe_int(r.get("passing_interceptions", 0))
        fumbles = _safe_int(r.get("rushing_fumbles_lost", 0)) + _safe_int(r.get("receiving_fumbles_lost", 0))
        turnovers = ints + fumbles

        comp = _safe_int(r.get("completions", 0))
        att = _safe_int(r.get("attempts", 0))

        td_conv = pd.to_numeric(r.get("third_down_converted", None), errors="coerce")
        td_att = pd.to_numeric(r.get("third_down_failed", None), errors="coerce")
        if pd.notna(td_conv) and pd.notna(td_att):
            third_down_str = f"{int(td_conv)}-{int(td_conv + td_att)}"
        else:
            third_down_str = "N/A"

        parsed[target_abbr] = {
            "totalYards": total_yds,
            "netPassingYards": pass_yds,
            "rushingYards": rush_yds,
            "firstDowns": first_downs if first_downs > 0 else "N/A",
            "turnovers": turnovers,
            "thirdDownEff": third_down_str,
            "completionAttempts": f"{comp}/{att}" if att > 0 else "N/A",
        }

    return parsed


def parse_nfl_player_leaders(week: int, away_abbr: str, home_abbr: str, year: int) -> dict:
    """Extracts Passing, Rushing, and Receiving yardage leaders with positions (QB, RB, WR, TE)."""
    df_players = fetch_nfl_player_stats(year=year)
    if df_players.empty:
        return {}

    sub = df_players[df_players["week"] == int(week)].copy() if "week" in df_players.columns else df_players.copy()
    leaders_by_team = {}

    for target_abbr in [away_abbr, home_abbr]:
        norm_t = normalize_nfl_abbr(target_abbr)
        t_df = sub[sub["team"].apply(normalize_nfl_abbr) == norm_t].copy()
        leaders_by_team[target_abbr] = {"passing": None, "rushing": None, "receiving": None}

        if t_df.empty:
            continue

        # Passing Leader
        if "passing_yards" in t_df.columns:
            p_df = t_df[pd.to_numeric(t_df["attempts"], errors="coerce").fillna(0) > 0].copy()
            if not p_df.empty:
                p_df["yds_num"] = pd.to_numeric(p_df["passing_yards"], errors="coerce").fillna(0)
                top = p_df.sort_values("yds_num", ascending=False).iloc[0]
                pos = str(top.get("position") or "QB").strip()
                name = str(top.get("player_display_name") or top.get("player_name") or "Unknown")
                comp = _safe_int(top.get("completions", 0))
                att = _safe_int(top.get("attempts", 0))
                yds = int(top["yds_num"])
                tds = _safe_int(top.get("passing_tds", 0))
                ints = _safe_int(top.get("passing_interceptions", 0))
                leaders_by_team[target_abbr]["passing"] = {
                    "player": f"{pos} {name}",
                    "yards": float(yds),
                    "summary": f"{pos} {name} ({comp}/{att}, {yds} YDS, {tds} TD, {ints} INT)",
                }

        # Rushing Leader
        if "rushing_yards" in t_df.columns:
            r_df = t_df[pd.to_numeric(t_df["carries"], errors="coerce").fillna(0) > 0].copy()
            if not r_df.empty:
                r_df["yds_num"] = pd.to_numeric(r_df["rushing_yards"], errors="coerce").fillna(0)
                top = r_df.sort_values("yds_num", ascending=False).iloc[0]
                pos = str(top.get("position") or "RB").strip()
                name = str(top.get("player_display_name") or top.get("player_name") or "Unknown")
                car = _safe_int(top.get("carries", 0))
                yds = int(top["yds_num"])
                tds = _safe_int(top.get("rushing_tds", 0))
                leaders_by_team[target_abbr]["rushing"] = {
                    "player": f"{pos} {name}",
                    "yards": float(yds),
                    "summary": f"{pos} {name} ({car} CAR, {yds} YDS, {tds} TD)",
                }

        # Receiving Leader
        if "receiving_yards" in t_df.columns:
            rec_df = t_df[pd.to_numeric(t_df["receptions"], errors="coerce").fillna(0) > 0].copy()
            if not rec_df.empty:
                rec_df["yds_num"] = pd.to_numeric(rec_df["receiving_yards"], errors="coerce").fillna(0)
                top = rec_df.sort_values("yds_num", ascending=False).iloc[0]
                pos = str(top.get("position") or "WR").strip()
                name = str(top.get("player_display_name") or top.get("player_name") or "Unknown")
                rec = _safe_int(top.get("receptions", 0))
                yds = int(top["yds_num"])
                tds = _safe_int(top.get("receiving_tds", 0))
                leaders_by_team[target_abbr]["receiving"] = {
                    "player": f"{pos} {name}",
                    "yards": float(yds),
                    "summary": f"{pos} {name} ({rec} REC, {yds} YDS, {tds} TD)",
                }

    return leaders_by_team


def build_nfl_plays_grid(
    df_pbp: pd.DataFrame,
    limit_plays=None,
    offense_filter="All Offenses",
    down_filter="All Downs",
    impact_filter="All Plays",
    away_abbr="",
    home_abbr="",
):
    """Transforms nflverse play-by-play DataFrame into the same grid & metrics schema as CFB."""
    if df_pbp.empty:
        return pd.DataFrame(), {"total": 0, "success_count": 0, "explosive_count": 0, "td_count": 0, "fg_count": 0, "to_count": 0}

    df = df_pbp.copy()
    if "play_id" in df.columns:
        df = df.sort_values(by="play_id", ascending=True).reset_index(drop=True)

    df["clean_down"] = pd.to_numeric(df.get("down"), errors="coerce").fillna(0).astype(int)
    df["clean_dist"] = pd.to_numeric(df.get("ydstogo"), errors="coerce").fillna(0).astype(int)
    df["clean_yds"] = pd.to_numeric(df.get("yards_gained"), errors="coerce").fillna(0).astype(int)

    def _fmt_qtr(q):
        try:
            if pd.isna(q):
                return "N/A"
            qi = int(float(q))
            return qi if qi <= 4 else f"OT{qi - 4}"
        except (ValueError, TypeError):
            return "N/A"

    df["Quarter"] = df["qtr"].apply(_fmt_qtr) if "qtr" in df.columns else "N/A"
    df["Time"] = df["time"].fillna("N/A").astype(str) if "time" in df.columns else "N/A"

    def _fmt_score(r):
        a_pts = pd.to_numeric(r.get("total_away_score"), errors="coerce")
        h_pts = pd.to_numeric(r.get("total_home_score"), errors="coerce")
        if pd.notna(a_pts) and pd.notna(h_pts):
            return f"{away_abbr} {int(a_pts)} - {home_abbr} {int(h_pts)}"
        return "N/A"

    df["Score"] = df.apply(_fmt_score, axis=1)

    def _classify_nfl_impact(r):
        is_td = _safe_int(r.get("touchdown", 0)) == 1
        fg_res = str(r.get("field_goal_result") or "").lower()
        is_fg = fg_res == "made"
        is_int = _safe_int(r.get("interception", 0)) == 1
        is_fum = _safe_int(r.get("fumble_lost", 0)) == 1
        is_to = is_int or is_fum

        if is_to and is_td:
            return "🚨🏆 DEF/ST TD"
        elif is_to:
            return "🚨 TURNOVER"
        elif is_td:
            return "🏆 TOUCHDOWN"
        elif is_fg:
            return "🎯 FIELD GOAL"
        return "Standard"

    df["Impact Play"] = df.apply(_classify_nfl_impact, axis=1)

    def _cat(ptype):
        s = str(ptype or "").lower()
        if s == "pass":
            return "Pass"
        elif s == "run":
            return "Run"
        elif s in ["field_goal", "punt", "kickoff", "extra_point"]:
            return "Special Teams"
        return "Other"

    df["play_category"] = df["play_type"].apply(_cat) if "play_type" in df.columns else "Other"
    df["Offense"] = df["posteam"].fillna("").astype(str) if "posteam" in df.columns else ""

    # Filter out non-play administrative rows (timeouts, quarter ends)
    df = df[(df["clean_down"] > 0) | (df["Impact Play"] != "Standard")].copy()

    if offense_filter != "All Offenses":
        norm_f = normalize_nfl_abbr(offense_filter)
        df = df[df["Offense"].apply(normalize_nfl_abbr) == norm_f]

    if down_filter != "All Downs":
        target_down = int(down_filter.split()[0][0])
        df = df[df["clean_down"] == target_down]

    if impact_filter == "Impact Plays Only (TDs, FGs, Turnovers)":
        df = df[df["Impact Play"] != "Standard"]
    elif impact_filter == "Scoring Plays Only":
        df = df[df["Impact Play"].str.contains("TOUCHDOWN|FIELD GOAL|DEF/ST TD")]
    elif impact_filter == "Turnovers Only":
        df = df[df["Impact Play"].str.contains("TURNOVER|DEF/ST TD")]

    def _eval_success(r):
        dn, ds, yd = r["clean_down"], r["clean_dist"], r["clean_yds"]
        if dn == 1:
            return yd >= (0.50 * ds)
        elif dn == 2:
            return yd >= (0.70 * ds)
        elif dn in [3, 4]:
            return yd >= ds
        return "TOUCHDOWN" in r["Impact Play"] or "FIELD GOAL" in r["Impact Play"]

    df["is_success"] = df.apply(_eval_success, axis=1)
    df["is_explosive"] = (
        ((df["play_category"] == "Pass") & (df["clean_yds"] >= 15))
        | ((df["play_category"] == "Run") & (df["clean_yds"] >= 10))
    )

    metrics = {
        "total": len(df),
        "success_count": int(df["is_success"].sum()) if len(df) > 0 else 0,
        "explosive_count": int(df["is_explosive"].sum()) if len(df) > 0 else 0,
        "td_count": int(df["Impact Play"].str.contains("TOUCHDOWN|DEF/ST TD").sum()) if len(df) > 0 else 0,
        "fg_count": int(df["Impact Play"].str.contains("FIELD GOAL").sum()) if len(df) > 0 else 0,
        "to_count": int(df["Impact Play"].str.contains("TURNOVER|DEF/ST TD").sum()) if len(df) > 0 else 0,
    }

    if len(df) == 0:
        return pd.DataFrame(), metrics

    sliced = df if limit_plays is None else df.head(limit_plays)
    disp = sliced.copy().reset_index(drop=True)
    disp["Success Status"] = disp["is_success"].apply(lambda x: "Yes" if x else "No")
    disp["Explosive Play"] = disp["is_explosive"].apply(lambda x: "Yes" if x else "No")
    disp["Play Description"] = disp["desc"].fillna("") if "desc" in disp.columns else ""

    final_grid = disp[
        [
            "Quarter",
            "Time",
            "Score",
            "Offense",
            "Impact Play",
            "play_category",
            "clean_down",
            "clean_dist",
            "clean_yds",
            "Success Status",
            "Explosive Play",
            "Play Description",
        ]
    ].copy()
    final_grid.columns = [
        "Quarter",
        "Time",
        "Score",
        "Offense",
        "Impact Play",
        "Play Category",
        "Down",
        "Distance",
        "Yards Gained",
        "Success Status",
        "Explosive Play",
        "Play Description",
    ]
    return final_grid, metrics
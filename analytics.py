import os
import json
import pandas as pd
from ingest import (
    get_secret,
    fetch_game_team_stats,
    fetch_game_player_stats,
    fetch_game_plays,
    fetch_team_roster,
)

CACHE_DIR = get_secret("OUTPUT_DIR", "./data")
os.makedirs(CACHE_DIR, exist_ok=True)

FBS_CONFERENCES = {
    "ACC": [
        "Boston College", "California", "Clemson", "Duke", "Florida State",
        "Georgia Tech", "Louisville", "Miami", "NC State", "North Carolina",
        "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia",
        "Virginia Tech", "Wake Forest",
    ],
    "American Athletic": [
        "Army", "Charlotte", "East Carolina", "Florida Atlantic", "Memphis",
        "Navy", "North Texas", "Rice", "South Florida", "Temple",
        "Tulane", "Tulsa", "UAB", "UTSA",
    ],
    "Big 12": [
        "Arizona", "Arizona State", "Baylor", "BYU", "Cincinnati",
        "Colorado", "Houston", "Iowa State", "Kansas", "Kansas State",
        "Oklahoma State", "TCU", "Texas Tech", "UCF", "Utah", "West Virginia",
    ],
    "Big Ten": [
        "Illinois", "Indiana", "Iowa", "Maryland", "Michigan",
        "Michigan State", "Minnesota", "Nebraska", "Northwestern", "Ohio State",
        "Oregon", "Penn State", "Purdue", "Rutgers", "UCLA",
        "USC", "Washington", "Wisconsin",
    ],
    "Conference USA": [
        "Delaware", "FIU", "Jacksonville State", "Kennesaw State", "Liberty",
        "Louisiana Tech", "Middle Tennessee", "Missouri State", "New Mexico State",
        "Sam Houston", "UTEP", "Western Kentucky",
    ],
    "FBS Independents": [
        "Notre Dame", "UConn",
    ],
    "Mid-American": [
        "Akron", "Ball State", "Bowling Green", "Buffalo", "Central Michigan",
        "Eastern Michigan", "Kent State", "Massachusetts", "Miami (OH)",
        "Northern Illinois", "Ohio", "Toledo", "Western Michigan",
    ],
    "Mountain West": [
        "Air Force", "Boise State", "Colorado State", "Fresno State", "Hawai'i",
        "Nevada", "New Mexico", "San Diego State", "San José State", "UNLV",
        "Utah State", "Wyoming",
    ],
    "Pac-12": [
        "Oregon State", "Washington State",
    ],
    "SEC": [
        "Alabama", "Arkansas", "Auburn", "Florida", "Georgia",
        "Kentucky", "LSU", "Mississippi State", "Missouri", "Oklahoma",
        "Ole Miss", "South Carolina", "Tennessee", "Texas", "Texas A&M",
        "Vanderbilt",
    ],
    "Sun Belt": [
        "App State", "Arkansas State", "Coastal Carolina", "Georgia Southern",
        "Georgia State", "James Madison", "Louisiana", "Marshall",
        "Old Dominion", "South Alabama", "Southern Miss", "Texas State",
        "Troy", "UL Monroe",
    ],
}


def _get_val(d: dict, *keys, default=None):
    """Safely fetches the first matching key (supports both snake_case and camelCase)."""
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def get_available_conferences(df_games: pd.DataFrame) -> list:
    """Returns sorted FBS conferences from df_games, falling back to FBS_CONFERENCES if null."""
    if df_games is not None and not df_games.empty:
        cols = df_games.columns.tolist()
        home_conf_key = next((c for c in cols if "conference" in c.lower() and "home" in c.lower()), None)
        if home_conf_key:
            confs = sorted(
                c for c in df_games[home_conf_key].dropna().unique().tolist()
                if str(c).strip() and str(c).strip().lower() != "none"
            )
            if confs:
                return confs
    return sorted(FBS_CONFERENCES.keys())


def get_teams_by_conference(df_games: pd.DataFrame, conference: str) -> list:
    if not conference:
        return []
    target = str(conference).strip().lower()
    teams = set()

    if df_games is not None and not df_games.empty:
        cols = df_games.columns.tolist()
        home_conf_key = next((c for c in cols if "conference" in c.lower() and "home" in c.lower()), None)
        away_conf_key = next((c for c in cols if "conference" in c.lower() and "away" in c.lower()), None)
        home_team_key = next((c for c in cols if "home_team" in c.lower() or "hometeam" in c.lower()), "home_team")
        away_team_key = next((c for c in cols if "away_team" in c.lower() or "awayteam" in c.lower()), "away_team")

        if home_conf_key and home_team_key in df_games.columns:
            h_matches = df_games[df_games[home_conf_key].fillna("").astype(str).str.lower() == target]
            teams.update(h_matches[home_team_key].dropna().unique().tolist())
        if away_conf_key and away_team_key in df_games.columns:
            a_matches = df_games[df_games[away_conf_key].fillna("").astype(str).str.lower() == target]
            teams.update(a_matches[away_team_key].dropna().unique().tolist())

    if teams:
        return sorted(teams)

    for conf_name, conf_teams in FBS_CONFERENCES.items():
        if conf_name.lower() == target:
            return sorted(conf_teams)
    return []


def get_team_schedule(df_games: pd.DataFrame, team_name: str) -> pd.DataFrame:
    if df_games is None or df_games.empty or not team_name:
        return pd.DataFrame()
    cols = df_games.columns.tolist()
    home_team_key = next((c for c in cols if "home_team" in c.lower() or "hometeam" in c.lower()), "home_team")
    away_team_key = next((c for c in cols if "away_team" in c.lower() or "awayteam" in c.lower()), "away_team")
    season_type_key = next((c for c in cols if "season_type" in c.lower() or "seasontype" in c.lower()), None)

    if home_team_key not in df_games.columns or away_team_key not in df_games.columns:
        return pd.DataFrame()

    target = str(team_name).strip().lower()
    sub = df_games[
        (df_games[home_team_key].fillna("").astype(str).str.lower() == target)
        | (df_games[away_team_key].fillna("").astype(str).str.lower() == target)
    ].copy()

    if sub.empty:
        return sub

    sub["_stype_ord"] = (
        sub[season_type_key].apply(lambda x: 1 if str(x).lower() == "postseason" else 0)
        if season_type_key
        else 0
    )
    if "week" in sub.columns:
        sub = sub.sort_values(by=["_stype_ord", "week"], ascending=[True, True])
    return sub.drop(columns=["_stype_ord"], errors="ignore")


def _load_or_fetch_team_stats(year: int, team_name: str, game_id) -> list:
    safe_team = "".join(c if c.isalnum() else "_" for c in str(team_name))
    cache_path = os.path.join(CACHE_DIR, f"box_{year}_{safe_team}.json")
    records = []

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    if not records:
        records = fetch_game_team_stats(year=year, team=team_name)
        if records:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(records, f, default=str)

    for r in records:
        gid = _get_val(r, "id", "game_id", "gameId")
        if str(gid) == str(game_id):
            return [r]

    direct = fetch_game_team_stats(year=year, game_id=game_id)
    return direct if direct else records


def parse_game_box_stats(game_id: int, team_name: str, year: int = 2026) -> dict:
    """Parses CFBD team box score stats into {school_name: {stat_key: stat_val}}."""
    records = _load_or_fetch_team_stats(year=year, team_name=team_name, game_id=game_id)
    if not records:
        return {}

    game_obj = records[0]
    teams_list = _get_val(game_obj, "teams", default=[])
    parsed = {}

    for t in teams_list:
        school = _get_val(t, "school", "team")
        if not school:
            continue
        stat_map = {}
        for s in _get_val(t, "stats", default=[]):
            cat = _get_val(s, "category", "name")
            val = _get_val(s, "stat", "value")
            if cat is not None:
                stat_map[str(cat)] = val
                stat_map[str(cat).lower().replace(" ", "").replace("_", "")] = val
        parsed[school] = stat_map

    return parsed


def _get_roster_position_map(team_name: str, year: int) -> dict:
    safe_team = "".join(c if c.isalnum() else "_" for c in str(team_name))
    cache_path = os.path.join(CACHE_DIR, f"roster_{year}_{safe_team}.json")
    roster = []

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                roster = json.load(f)
        except Exception:
            roster = []

    if not roster:
        roster = fetch_team_roster(team=team_name, year=year)
        if roster:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(roster, f, default=str)

    pos_map = {}
    for p in roster:
        pid = _get_val(p, "id", "player_id", "playerId")
        first = str(_get_val(p, "first_name", "firstName", default="")).strip()
        last = str(_get_val(p, "last_name", "lastName", default="")).strip()
        full = f"{first} {last}".strip()
        pos = str(_get_val(p, "position", default="")).strip()
        if pid is not None and pos:
            pos_map[str(pid)] = pos
        if full and pos:
            pos_map[full.lower()] = pos
    return pos_map


def parse_game_player_leaders(game_id: int, team_name: str, year: int = 2026) -> dict:
    """Extracts Passing, Rushing, and Receiving yardage leaders per team with roster positions."""
    safe_team = "".join(c if c.isalnum() else "_" for c in str(team_name))
    cache_path = os.path.join(CACHE_DIR, f"players_{year}_{safe_team}.json")
    records = []

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    if not records:
        records = fetch_game_player_stats(year=year, team=team_name)
        if records:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(records, f, default=str)

    game_obj = next(
        (r for r in records if str(_get_val(r, "id", "game_id", "gameId")) == str(game_id)),
        None,
    )
    if not game_obj:
        direct = fetch_game_player_stats(year=year, game_id=game_id)
        game_obj = direct[0] if direct else None
    if not game_obj:
        return {}

    leaders_by_team = {}
    default_pos = {"passing": "QB", "rushing": "RB", "receiving": "WR"}

    for t in _get_val(game_obj, "teams", default=[]):
        school = _get_val(t, "school", "team")
        if not school:
            continue
        pos_map = _get_roster_position_map(school, year)
        leaders_by_team[school] = {"passing": None, "rushing": None, "receiving": None}

        for cat_obj in _get_val(t, "categories", default=[]):
            cat_name = str(_get_val(cat_obj, "name", default="")).lower()
            if cat_name not in ["passing", "rushing", "receiving"]:
                continue

            athlete_stats = {}
            for typ in _get_val(cat_obj, "types", default=[]):
                t_name = str(_get_val(typ, "name", default="")).upper()
                for ath in _get_val(typ, "athletes", default=[]):
                    aid = str(_get_val(ath, "id", default=_get_val(ath, "name", default="")))
                    aname = str(_get_val(ath, "name", default="Unknown")).strip()
                    stat_val = str(_get_val(ath, "stat", default="0")).strip()
                    if aid not in athlete_stats:
                        athlete_stats[aid] = {"id": aid, "name": aname}
                    athlete_stats[aid][t_name] = stat_val

            best_ath = None
            best_yds = -9999.0
            for ath in athlete_stats.values():
                try:
                    yds = float(ath.get("YDS", 0))
                except ValueError:
                    yds = 0.0
                if yds > best_yds:
                    best_yds = yds
                    best_ath = ath

            if best_ath and best_yds > -9999.0:
                aname = best_ath["name"]
                aid = best_ath["id"]
                pos = pos_map.get(aid) or pos_map.get(aname.lower()) or default_pos[cat_name]
                yds_int = int(best_yds)

                if cat_name == "passing":
                    c_att = best_ath.get("C/ATT", "0/0")
                    tds = best_ath.get("TD", "0")
                    ints = best_ath.get("INT", "0")
                    summary = f"{pos} {aname} ({c_att}, {yds_int} YDS, {tds} TD, {ints} INT)"
                elif cat_name == "rushing":
                    car = best_ath.get("CAR", "0")
                    tds = best_ath.get("TD", "0")
                    summary = f"{pos} {aname} ({car} CAR, {yds_int} YDS, {tds} TD)"
                else:
                    rec = best_ath.get("REC", "0")
                    tds = best_ath.get("TD", "0")
                    summary = f"{pos} {aname} ({rec} REC, {yds_int} YDS, {tds} TD)"

                leaders_by_team[school][cat_name] = {
                    "player": f"{pos} {aname}",
                    "yards": float(yds_int),
                    "summary": summary,
                }

    return leaders_by_team


def get_game_plays_df(game_id: int, week: int, team_name: str, year: int = 2026) -> pd.DataFrame:
    """Fetches CFB play-by-play data and normalizes camelCase/snake_case keys for app.py."""
    cache_path = os.path.join(CACHE_DIR, f"plays_{year}_{game_id}.json")
    plays = []

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                plays = json.load(f)
        except Exception:
            plays = []

    if not plays:
        plays = fetch_game_plays(year=year, week=week, team=team_name, game_id=game_id)
        if plays:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(plays, f, default=str)

    if not plays:
        return pd.DataFrame()

    df = pd.DataFrame(plays)

    rename_map = {
        "offenseTeam": "offense_team",
        "playType": "play_type",
        "yardsGained": "yards_gained",
        "playText": "play_text",
        "driveNumber": "drive_number",
        "playNumber": "play_number",
        "offenseScore": "offense_score",
        "defenseScore": "defense_score",
    }
    for src_col, dst_col in rename_map.items():
        if src_col in df.columns and dst_col not in df.columns:
            df[dst_col] = df[src_col]

    return df
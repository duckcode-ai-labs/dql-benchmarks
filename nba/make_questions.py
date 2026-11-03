"""The 40 NBA questions and their gold SQL, written before any ZLens answer was run or read.

    python3 nba/make_questions.py   # writes nba/questions.json

Gold policy (the owner's local_ layer and local_duckdb/oracle.json agree on it):
- A season is the SEASON column: the season that starts in that year. Every game in
  the data counts, preseason and playoffs included, as in the owner's local_ layer and
  oracle. GAME_ID's first digit encodes the game type (1 preseason, 2 regular, 4
  playoffs, 5 play-in), so a question that means every game says so (gold audit).
- Duplicate source rows count once (raw_games has 29 repeated games and
  raw_games_details 289 repeated player rows, all in season 2020).
- A player played in a game only when the row has no COMMENT and at least one stat
  (the `participated` flag). DNP rows are not games played and add no stats.
- A double-double is a participating game with at least two of points, rebounds,
  assists, steals and blocks at 10 or more; a triple-double needs three.

`needs` lists what the answer must read, as groups of alternatives: a question is
"recalled" when every group has at least one of its tables in front of the drafter.
`layer` names the trap when the layer matters.
"""

import json
from pathlib import Path

T = "TRANSFORMED"
PG = f"{T}.local_player_game_facts"
PS = f"{T}.local_player_season_facts"
TG = f"{T}.local_team_game_facts"
TS = f"{T}.local_team_season_facts"
TEAMS = "RAW.raw_teams"

# Alternatives an answer may read for each need.
TEAM_NAMES = ["raw.raw_teams", "transformed.dim_teams_cleansed", "transformed.src_teams", "dev.scd_raw_teams"]
PLAYER_GAMES = ["transformed.local_player_game_facts", "raw.raw_games_details", "transformed.src_games_details", "transformed.int_player_stats"]
PLAYER_SEASONS = ["transformed.local_player_season_facts", "transformed.local_player_game_facts", "raw.raw_games_details", "transformed.src_games_details",
                  "transformed.fct_player_performance", "transformed.fct_player_journey", "transformed.int_season_stats", "transformed.int_player_stats"]
GAMES = ["transformed.local_team_game_facts", "raw.raw_games", "transformed.src_games", "transformed.local_player_game_facts"]
TEAM_SEASONS = ["transformed.local_team_season_facts", "transformed.local_team_game_facts", "raw.raw_games", "transformed.src_games"]
# A season join for player rows that carry no season of their own.
GAME_SEASON = ["transformed.local_player_game_facts", "raw.raw_games", "transformed.src_games", "transformed.local_team_game_facts", "transformed.int_player_stats"]

Q = []
# The game scope every season question states (gold audit, 2026-11-03).
ALL = "counting every game in the data, preseason and playoffs included"


def q(category, question, sql, needs, layer=None, oracle=None):
    Q.append({
        "question_id": len(Q) + 1,
        "category": category,
        "question": question,
        "SQL": " ".join(sql.split()),
        "needs": needs,
        **({"layer": layer} if layer else {}),
        **({"oracle": oracle} if oracle else {}),
    })


# ---------------------------------------------------------------- lookups (6)
q("lookup", "What arena do the Golden State Warriors play in?",
  f"SELECT ARENA FROM {TEAMS} WHERE ABBREVIATION = 'GSW'", [TEAM_NAMES])
q("lookup", "Who is listed as the head coach of the Boston Celtics in the teams data?",
  f"SELECT HEADCOACH FROM {TEAMS} WHERE ABBREVIATION = 'BOS'", [TEAM_NAMES])
q("lookup", "What founding year does the teams data list for the San Antonio Spurs?",
  f"SELECT YEARFOUNDED FROM {TEAMS} WHERE ABBREVIATION = 'SAS'", [TEAM_NAMES])
q("lookup", "What are the earliest and latest game dates in the data?",
  f"SELECT MIN(game_date) AS first_game, MAX(game_date) AS last_game FROM {TG}", [GAMES],
  oracle="calendar_coverage")
q("lookup", "How many points did LeBron James score in the game on June 19, 2016?",
  f"SELECT points FROM {PG} WHERE player_name = 'LeBron James' AND game_date = DATE '2016-06-19'", [PLAYER_GAMES, GAME_SEASON])
q("lookup", "Which team has the largest arena capacity? Give the team abbreviation and the capacity.",
  f"SELECT ABBREVIATION, ARENACAPACITY FROM {TEAMS} ORDER BY ARENACAPACITY DESC NULLS LAST LIMIT 1", [TEAM_NAMES])

# ------------------------------------------------------------ aggregates (10)
q("aggregate", f"Who scored the most points in the 2017 season, {ALL}, and how many points?",
  f"SELECT player_name, total_points FROM {PS} WHERE season = 2017 ORDER BY total_points DESC LIMIT 1", [PLAYER_SEASONS],
  oracle="top_scorers_2017")
q("aggregate", f"How many games were played in the 2019 season, {ALL}?",
  f"SELECT COUNT(DISTINCT game_id) AS games FROM {TG} WHERE season = 2019", [GAMES])
q("aggregate", f"Who are the top 5 scorers across all seasons by total points, {ALL}? Give each player's name and total points.",
  f"SELECT MIN(player_name) AS player_name, SUM(total_points) AS total_points FROM {PS} GROUP BY player_id ORDER BY total_points DESC LIMIT 5",
  [PLAYER_SEASONS], oracle="multi_season_weighted_ppg")
q("aggregate", f"How many three-pointers were made in total in the 2015 season, {ALL}?",
  f"SELECT SUM(total_three_pointers_made) AS threes FROM {PS} WHERE season = 2015", [PLAYER_SEASONS])
q("aggregate", f"Which player had the most assists in the 2010 season, {ALL}, and how many?",
  f"SELECT player_name, total_assists FROM {PS} WHERE season = 2010 ORDER BY total_assists DESC LIMIT 1", [PLAYER_SEASONS])
q("aggregate", f"How many points were scored in total in the 2012 season, counting both teams and {ALL}?",
  f"SELECT SUM(team_points) AS points FROM {TG} WHERE season = 2012", [GAMES])
q("aggregate", "What is the most points one player scored in a single game in the data, and who scored them?",
  f"SELECT player_name, points FROM {PG} WHERE participated ORDER BY points DESC LIMIT 1", [PLAYER_GAMES])
q("aggregate", "Which season had the most games in the data?",
  f"SELECT season FROM {TG} GROUP BY season ORDER BY COUNT(DISTINCT game_id) DESC LIMIT 1", [GAMES])
q("aggregate", f"What was the average number of points a team scored per game in the 2021 season, {ALL}? Round to two decimals.",
  f"SELECT ROUND(AVG(team_points), 2) AS avg_points FROM {TG} WHERE season = 2021", [GAMES])
q("aggregate", f"Which player blocked the most shots in the 2008 season, {ALL}, and how many blocks?",
  f"SELECT player_name, total_blocks FROM {PS} WHERE season = 2008 ORDER BY total_blocks DESC LIMIT 1", [PLAYER_SEASONS],
  layer="the fct_ and int_ tables hold only seasons 2009 to 2019")

# --------------------------------------------------------------- layer (10)
q("layer", f"How many games did LeBron James play in the 2017 season, {ALL}?",
  f"SELECT games_played FROM {PS} WHERE player_name = 'LeBron James' AND season = 2017", [PLAYER_SEASONS],
  layer="fct_player_performance and int_season_stats count DNP rows as games (108, not 105)", oracle="top_scorers_2017")
q("layer", f"What were Stephen Curry's points per game in the 2019 season, {ALL}? Round to two decimals.",
  f"SELECT ROUND(total_points / games_played, 2) AS ppg FROM {PS} WHERE player_name = 'Stephen Curry' AND season = 2019", [PLAYER_SEASONS],
  layer="fct_player_performance divides by 12 games including 3 DNPs (17.58, not 23.44)")
q("layer", f"How many games were played in the 2020 season, {ALL}?",
  f"SELECT COUNT(DISTINCT game_id) AS games FROM {TG} WHERE season = 2020", [GAMES],
  layer="raw_games and src_games repeat 29 games of 2020 (1,249 rows for 1,220 games)")
q("layer", f"How many points did Jayson Tatum score in total in the 2020 season, {ALL}?",
  f"SELECT total_points FROM {PS} WHERE player_name = 'Jayson Tatum' AND season = 2020", [PLAYER_SEASONS],
  layer="raw_games_details repeats 4 of his 2020 games (2,024, not 1,924); fct_ has no 2020")
q("layer", f"Which five players had the best field goal percentage in the 2017 season, {ALL}, among players with at least 100 field goal attempts? Give each name and the percentage as a fraction rounded to three decimals.",
  f"SELECT player_name, ROUND(total_field_goals_made / total_field_goals_attempted, 3) AS fg_pct FROM {PS} WHERE season = 2017 AND total_field_goals_attempted >= 100 ORDER BY total_field_goals_made / total_field_goals_attempted DESC, player_id LIMIT 5",
  [PLAYER_SEASONS], layer="fct_ avg_field_goal_pct averages per-game percentages", oracle="field_goal_leaders_2017")
q("layer", f"How many players took the floor (not DNP) in at least one game in the 2021 season, {ALL}?",
  f"SELECT COUNT(*) AS players FROM {PS} WHERE season = 2021 AND games_played > 0", [PLAYER_SEASONS],
  layer="players with only DNP rows are in the game rows and in local_player_season_facts with games_played = 0")
q("layer", f"How many players took the floor for more than one team in the 2019 season, {ALL}?",
  f"SELECT COUNT(*) AS players FROM {PS} WHERE season = 2019 AND teams_played > 1", [PLAYER_SEASONS],
  layer="a team counts only when the player took the floor for it")
q("layer", f"Who scored the most points in the 2005 season, {ALL}, and how many?",
  f"SELECT player_name, total_points FROM {PS} WHERE season = 2005 ORDER BY total_points DESC LIMIT 1", [PLAYER_SEASONS],
  layer="the fct_ and int_ tables hold only seasons 2009 to 2019")
q("layer", f"Who had the highest points per game in the 2017 season among players with at least 20 games played, {ALL}? Give the name and points per game rounded to two decimals.",
  f"SELECT player_name, ROUND(points_per_game, 2) AS ppg FROM {PS} WHERE season = 2017 AND games_played >= 20 ORDER BY points_per_game DESC LIMIT 1",
  [PLAYER_SEASONS], layer="games played must leave out DNP rows", oracle="points_per_game_leaders_2017_min20")
q("layer", f"How many games did the Brooklyn Nets win in the 2020 season, {ALL}?",
  f"SELECT ts.wins FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE t.ABBREVIATION = 'BKN' AND ts.season = 2020",
  [TEAM_SEASONS, TEAM_NAMES], layer="raw_games repeats 5 Brooklyn games of 2020 (59 wins counting rows, not 57)")

# ----------------------------------------------------------- vocabulary (8)
q("vocabulary", f"Who had the most double-doubles in the 2017 season, {ALL}, and how many?",
  f"SELECT player_name, double_double_games FROM {PS} WHERE season = 2017 ORDER BY double_double_games DESC LIMIT 1", [PLAYER_SEASONS],
  oracle="double_double_leaders_2017")
q("vocabulary", "What is the home win rate across all games in the data that have a final score, as a fraction rounded to three decimals?",
  f"SELECT ROUND(AVG(CASE WHEN team_won THEN 1.0 ELSE 0.0 END), 3) AS home_win_rate FROM {TG} WHERE is_home AND team_points IS NOT NULL AND opponent_points IS NOT NULL", [GAMES])
q("vocabulary", f"Which team had the best home win rate in the 2018 season, {ALL}? Give the team abbreviation and the rate as a fraction rounded to three decimals.",
  f"SELECT t.ABBREVIATION, ROUND(ts.home_wins / ts.home_games, 3) AS home_win_rate FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE ts.season = 2018 ORDER BY ts.home_wins / ts.home_games DESC LIMIT 1",
  [TEAM_SEASONS, TEAM_NAMES])
q("vocabulary", f"How many triple-doubles did Russell Westbrook have in the 2016 season, {ALL}?",
  f"SELECT COUNT(*) AS triple_doubles FROM {PG} WHERE player_name = 'Russell Westbrook' AND season = 2016 AND participated AND "
  "((points >= 10)::INT + (rebounds >= 10)::INT + (assists >= 10)::INT + (steals >= 10)::INT + (blocks >= 10)::INT) >= 3",
  [PLAYER_GAMES, GAME_SEASON])
q("vocabulary", f"What was Giannis Antetokounmpo's points per game in the 2019 season, {ALL}? Round to two decimals.",
  f"SELECT ROUND(points_per_game, 2) AS ppg FROM {PS} WHERE player_name = 'Giannis Antetokounmpo' AND season = 2019", [PLAYER_SEASONS],
  layer="fct_player_performance counts 2 DNP rows as games (28.08, not 28.79)")
q("vocabulary", f"Which team had the biggest total point differential (points scored minus points allowed) in the 2016 season, {ALL}? Give the team abbreviation and the differential.",
  f"SELECT t.ABBREVIATION, ts.point_differential FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE ts.season = 2016 ORDER BY ts.point_differential DESC LIMIT 1",
  [TEAM_SEASONS, TEAM_NAMES])
q("vocabulary", f"Who had the most double-doubles across all seasons, {ALL}, and how many?",
  f"SELECT MIN(player_name) AS player_name, SUM(double_double_games) AS double_doubles FROM {PS} GROUP BY player_id ORDER BY double_doubles DESC LIMIT 1",
  [PLAYER_SEASONS])
q("vocabulary", f"How many 50-point games were there across all seasons, {ALL}?",
  f"SELECT COUNT(*) AS fifty_point_games FROM {PG} WHERE participated AND points >= 50", [PLAYER_GAMES])

# ---------------------------------------------------------------- joins (6)
q("join", f"Which team won the most games in the 2017 season, {ALL}? Give the team abbreviation and the number of wins.",
  f"SELECT t.ABBREVIATION, ts.wins FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE ts.season = 2017 ORDER BY ts.wins DESC LIMIT 1",
  [TEAM_SEASONS, TEAM_NAMES], oracle="team_win_leaders_2017")
q("join", f"Who is listed as the head coach of the team that won the most games in the 2018 season, {ALL}?",
  f"SELECT t.HEADCOACH FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE ts.season = 2018 ORDER BY ts.wins DESC LIMIT 1",
  [TEAM_SEASONS, TEAM_NAMES])
q("join", "Which arena hosted the most games in the 2019 season?",
  f"SELECT t.ARENA FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE ts.season = 2019 GROUP BY t.ARENA ORDER BY SUM(ts.home_games) DESC LIMIT 1",
  [TEAM_SEASONS, TEAM_NAMES])
q("join", f"What were LeBron James' points per game against the Boston Celtics across all seasons, {ALL}? Round to two decimals.",
  f"SELECT ROUND(AVG(pg.points), 2) AS ppg FROM {PG} pg JOIN {TEAMS} t ON t.TEAM_ID = pg.opponent_team_id WHERE pg.player_name = 'LeBron James' AND t.ABBREVIATION = 'BOS' AND pg.participated",
  [PLAYER_GAMES, TEAM_NAMES])
q("join", f"Against which team did Kevin Durant score the most total points across all seasons, {ALL}? Give the team abbreviation and the points.",
  f"SELECT t.ABBREVIATION, SUM(pg.points) AS points FROM {PG} pg JOIN {TEAMS} t ON t.TEAM_ID = pg.opponent_team_id WHERE pg.player_name = 'Kevin Durant' AND pg.participated GROUP BY t.ABBREVIATION ORDER BY points DESC LIMIT 1",
  [PLAYER_GAMES, TEAM_NAMES])
q("join", f"Which team scored the most total points in the 2021 season, {ALL}? Give the team abbreviation and the points.",
  f"SELECT t.ABBREVIATION, ts.total_points FROM {TS} ts JOIN {TEAMS} t ON t.TEAM_ID = ts.team_id WHERE ts.season = 2021 ORDER BY ts.total_points DESC LIMIT 1",
  [TEAM_SEASONS, TEAM_NAMES])

assert len(Q) == 40, len(Q)
Path(__file__).with_name("questions.json").write_text(json.dumps(Q, indent=1) + "\n")
print(f"wrote {len(Q)} questions")

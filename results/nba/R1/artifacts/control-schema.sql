CREATE TABLE RAW.raw_games (
  GAME_DATE_EST DATE,
  GAME_ID BIGINT,
  GAME_STATUS_TEXT VARCHAR,
  HOME_TEAM_ID BIGINT,
  VISITOR_TEAM_ID BIGINT,
  SEASON INTEGER,
  TEAM_ID_home BIGINT,
  PTS_home DOUBLE,
  FG_PCT_home DOUBLE,
  FT_PCT_home DOUBLE,
  FG3_PCT_home DOUBLE,
  AST_home DOUBLE,
  REB_home DOUBLE,
  TEAM_ID_away BIGINT,
  PTS_away DOUBLE,
  FG_PCT_away DOUBLE,
  FT_PCT_away DOUBLE,
  FG3_PCT_away DOUBLE,
  AST_away DOUBLE,
  REB_away DOUBLE,
  HOME_TEAM_WINS INTEGER
);

CREATE TABLE RAW.raw_games_details (
  GAME_ID BIGINT,
  TEAM_ID BIGINT,
  TEAM_ABBREVIATION VARCHAR,
  TEAM_CITY VARCHAR,
  PLAYER_ID BIGINT,
  PLAYER_NAME VARCHAR,
  NICKNAME VARCHAR,
  START_POSITION VARCHAR,
  COMMENT VARCHAR,
  MIN VARCHAR,
  FGM DOUBLE,
  FGA DOUBLE,
  FG_PCT DOUBLE,
  FG3M DOUBLE,
  FG3A DOUBLE,
  FG3_PCT DOUBLE,
  FTM DOUBLE,
  FTA DOUBLE,
  FT_PCT DOUBLE,
  OREB DOUBLE,
  DREB DOUBLE,
  REB DOUBLE,
  AST DOUBLE,
  STL DOUBLE,
  BLK DOUBLE,
  TO DOUBLE,
  PF DOUBLE,
  PTS DOUBLE,
  PLUS_MINUS DOUBLE,
  TTO DOUBLE
);

CREATE TABLE RAW.raw_player_information (
  TeamID BIGINT,
  SEASON INTEGER,
  LeagueID VARCHAR,
  PLAYER VARCHAR,
  POSITION VARCHAR,
  HEIGHT VARCHAR,
  WEIGHT DOUBLE,
  BIRTH_DATE VARCHAR,
  AGE DOUBLE,
  SCHOOL VARCHAR
);

-- Raw player data from NBA games
CREATE TABLE RAW.raw_players (
  PLAYER_NAME VARCHAR,
  TEAM_ID BIGINT,
  PLAYER_ID BIGINT,
  SEASON INTEGER
);

CREATE TABLE RAW.raw_ranking (
  TEAM_ID BIGINT,
  LEAGUE_ID VARCHAR,
  SEASON_ID INTEGER,
  STANDINGSDATE DATE,
  CONFERENCE VARCHAR,
  TEAM VARCHAR,
  G INTEGER,
  W INTEGER,
  L INTEGER,
  W_PCT DOUBLE,
  HOME_RECORD VARCHAR,
  ROAD_RECORD VARCHAR,
  RETURNTOPLAY VARCHAR
);

-- Raw team data from NBA games
CREATE TABLE RAW.raw_teams (
  LEAGUE_ID VARCHAR,
  TEAM_ID BIGINT,
  MIN_YEAR INTEGER,
  MAX_YEAR INTEGER,
  ABBREVIATION VARCHAR,
  NICKNAME VARCHAR,
  YEARFOUNDED INTEGER,
  CITY VARCHAR,
  ARENA VARCHAR,
  ARENACAPACITY INTEGER,
  OWNER VARCHAR,
  GENERALMANAGER VARCHAR,
  HEADCOACH VARCHAR,
  DLEAGUEAFFILIATION VARCHAR
);

-- This dimension table holds cleansed data about players.
CREATE VIEW TRANSFORMED.dim_players_cleansed (
  player_id BIGINT,  -- The unique identifier of the player.
  team_id BIGINT,  -- The unique identifier of the team to which the player belongs.
  PLAYER_NAME VARCHAR,  -- The name of the player.
  SEASON INTEGER  -- The sporting season during which the statistics were recorded.
);

-- This dimension table holds data about different sports seasons.
CREATE VIEW TRANSFORMED.dim_seasons (
  season_id INTEGER,  -- The unique identifier of the sports season.
  season_name INTEGER,  -- The name of the sports season.
  start_date DATE,  -- The start date of the sports season.
  end_date DATE  -- The end date of the sports season.
);

CREATE VIEW TRANSFORMED.dim_teams_cleansed (
  league_id INTEGER,
  team_id INTEGER,
  min_year INTEGER,
  max_year INTEGER,
  team_abbreviation VARCHAR,
  team_nickname VARCHAR,
  year_founded INTEGER,
  city VARCHAR,
  arena VARCHAR,
  arena_capacity INTEGER,
  team_owner VARCHAR,
  general_manager VARCHAR,
  head_coach VARCHAR,
  dleague_affiliation VARCHAR
);

-- Season-by-season journey for every NBA player. One row represents one player's performance in one NBA season. Grain: (player_id, season) — periodic snapshot fact.
CREATE TABLE TRANSFORMED.fct_player_journey (
  player_id BIGINT,  -- Surrogate identifier for the player, sourced from src_players.
  player_name VARCHAR,  -- Full name of the player.
  season INTEGER,  -- NBA season year (integer).
  career_season_number BIGINT,  -- Ordinal position of this season in the player's career. 1 = rookie season; increments by 1 for each subsequent season ordered ascending.
  total_points DOUBLE,  -- Total points scored by the player in this season.
  total_assists DOUBLE,  -- Total assists recorded by the player in this season.
  total_rebounds DOUBLE,  -- Total rebounds recorded by the player in this season.
  total_steals DOUBLE,  -- Total steals recorded by the player in this season.
  total_blocks DOUBLE,  -- Total blocks recorded by the player in this season.
  total_turnovers DOUBLE,  -- Total turnovers recorded by the player in this season.
  total_personal_fouls DOUBLE,  -- Total personal fouls recorded by the player in this season.
  total_field_goals_made DOUBLE,  -- Total field goals made by the player in this season.
  total_field_goals_attempted DOUBLE,  -- Total field goals attempted by the player in this season.
  total_three_points_made DOUBLE,  -- Total three-point field goals made by the player in this season.
  total_three_points_attempted DOUBLE,  -- Total three-point field goals attempted by the player in this season.
  total_free_throws_made DOUBLE,  -- Total free throws made by the player in this season.
  total_free_throws_attempted DOUBLE,  -- Total free throws attempted by the player in this season.
  avg_field_goal_pct DOUBLE,  -- Average field goal percentage across games played in this season.
  avg_free_throw_pct DOUBLE,  -- Average free throw percentage across games played in this season.
  avg_three_point_pct DOUBLE,  -- Average three-point percentage across games played in this season.
  games_played BIGINT,  -- Number of distinct games played by the player in this season.
  efficiency_rating DOUBLE,  -- Player efficiency rating (EFF) for the season. Formula: (PTS + REB + AST + STL + BLK - missed FG - missed FT - TOV) / games_played. NULL when games_played = 0.
  pts_delta DOUBLE,  -- Season-over-season change in total points (current season minus prior season). NULL for a player's first (rookie) season.
  ast_delta DOUBLE,  -- Season-over-season change in total assists (current season minus prior season). NULL for a player's first (rookie) season.
  reb_delta DOUBLE,  -- Season-over-season change in total rebounds (current season minus prior season). NULL for a player's first (rookie) season.
  efficiency_delta DOUBLE,  -- Season-over-season change in efficiency rating (current season minus prior season). NULL for a player's first (rookie) season.
  career_pts DOUBLE,  -- Cumulative career points through and including this season.
  career_ast DOUBLE,  -- Cumulative career assists through and including this season.
  career_reb DOUBLE,  -- Cumulative career rebounds through and including this season.
  career_games_played HUGEINT,  -- Cumulative career games played through and including this season.
  team_id BIGINT,  -- Team identifier for this player's season. For players on multiple teams in a season, reflects the first team alphabetically by team_id (v1 policy). NULL when no bio record exists in stg_player_information.
  player_position VARCHAR,  -- Player's listed position (e.g. G, F, C). NULL when bio record is absent.
  height_cm DECIMAL(15,2),  -- Player height in centimetres, converted from feet-inches. NULL when bio record is absent.
  weight DOUBLE,  -- Player weight. NULL when bio record is absent.
  birth_date DATE,  -- Player date of birth. NULL when bio record is absent.
  age DOUBLE,  -- Player age at time of bio record. NULL when bio record is absent.
  school VARCHAR  -- College or school the player attended. NULL when bio record is absent.
);

CREATE TABLE TRANSFORMED.fct_player_performance (
  player_id BIGINT,
  player_name VARCHAR,
  season INTEGER,
  total_points DOUBLE,
  total_assists DOUBLE,
  total_rebounds DOUBLE,
  avg_field_goal_pct DOUBLE,
  avg_free_throw_pct DOUBLE,
  avg_three_point_pct DOUBLE,
  total_field_goals_made DOUBLE,
  total_field_goals_attempted DOUBLE,
  total_three_points_made DOUBLE,
  total_three_points_attempted DOUBLE,
  total_free_throws_made DOUBLE,
  total_free_throws_attempted DOUBLE,
  total_steals DOUBLE,
  total_blocks DOUBLE,
  total_turnovers DOUBLE,
  total_personal_fouls DOUBLE,
  games_played BIGINT,
  efficiency_rating DOUBLE,
  points_per_game DOUBLE,
  assists_per_game DOUBLE,
  rebounds_per_game DOUBLE,
  steals_per_game DOUBLE,
  blocks_per_game DOUBLE,
  turnovers_per_game DOUBLE,
  effective_field_goal_pct DOUBLE,
  true_shooting_pct DOUBLE,
  PLAYER_POSITION VARCHAR,
  HEIGHT DECIMAL(15,2),
  WEIGHT DOUBLE,
  BIRTH_DATE DATE,
  AGE DOUBLE,
  SCHOOL VARCHAR
);

CREATE TABLE TRANSFORMED.int_player_stats (
  player_id BIGINT,
  player_name VARCHAR,
  DETAILS_GAME_ID VARCHAR,
  game_date_est DATE,
  season INTEGER,
  home_team_wins INTEGER,
  game_status_text VARCHAR,
  fgm DOUBLE,
  fga DOUBLE,
  fg_pct DOUBLE,
  fg3m DOUBLE,
  fg3a DOUBLE,
  fg3_pct DOUBLE,
  ftm DOUBLE,
  fta DOUBLE,
  ft_pct DOUBLE,
  pts DOUBLE,
  ast DOUBLE,
  reb DOUBLE,
  stl DOUBLE,
  blk DOUBLE,
  turnover DOUBLE,
  pf DOUBLE,
  plus_minus DOUBLE
);

CREATE TABLE TRANSFORMED.int_season_stats (
  player_id BIGINT,
  player_name VARCHAR,
  season INTEGER,
  total_points DOUBLE,
  total_assists DOUBLE,
  total_rebounds DOUBLE,
  avg_field_goal_pct DOUBLE,
  avg_free_throw_pct DOUBLE,
  avg_three_point_pct DOUBLE,
  total_field_goals_made DOUBLE,
  total_field_goals_attempted DOUBLE,
  total_three_points_made DOUBLE,
  total_three_points_attempted DOUBLE,
  total_free_throws_made DOUBLE,
  total_free_throws_attempted DOUBLE,
  total_steals DOUBLE,
  total_blocks DOUBLE,
  total_turnovers DOUBLE,
  total_personal_fouls DOUBLE,
  games_played BIGINT,
  missed_field_goals DOUBLE,
  missed_free_throws DOUBLE,
  efficiency_rating DOUBLE
);

-- Local DuckDB full-history player-game fact. Grain is one row per (game_id, team_id, player_id). DNP/comment rows are retained with participated=false; duplicate source records use one deterministic canonical row.
CREATE TABLE TRANSFORMED.local_player_game_facts (
  game_id BIGINT,
  game_date DATE,
  season INTEGER,
  team_id BIGINT,
  opponent_team_id BIGINT,
  is_home BOOLEAN,
  home_team_wins INTEGER,
  game_status_text VARCHAR,
  player_id BIGINT,
  player_name VARCHAR,
  comment_text VARCHAR,
  minutes_text VARCHAR,
  participated BOOLEAN,
  field_goals_made DOUBLE,
  field_goals_attempted DOUBLE,
  field_goal_pct DOUBLE,
  three_pointers_made DOUBLE,
  three_pointers_attempted DOUBLE,
  three_point_pct DOUBLE,
  free_throws_made DOUBLE,
  free_throws_attempted DOUBLE,
  free_throw_pct DOUBLE,
  offensive_rebounds DOUBLE,
  defensive_rebounds DOUBLE,
  rebounds DOUBLE,
  assists DOUBLE,
  steals DOUBLE,
  blocks DOUBLE,
  turnovers DOUBLE,
  personal_fouls DOUBLE,
  points DOUBLE,
  plus_minus DOUBLE
);

-- Local DuckDB full-history player-season aggregate. Grain is one row per player_id and source season. Totals and games_played use participated player-game rows only.
CREATE TABLE TRANSFORMED.local_player_season_facts (
  player_id BIGINT,
  player_name VARCHAR,
  season INTEGER,
  first_game_date DATE,
  last_game_date DATE,
  games_played BIGINT,
  teams_played BIGINT,
  total_field_goals_made DOUBLE,
  total_field_goals_attempted DOUBLE,
  total_three_pointers_made DOUBLE,
  total_three_pointers_attempted DOUBLE,
  total_free_throws_made DOUBLE,
  total_free_throws_attempted DOUBLE,
  total_points DOUBLE,
  total_assists DOUBLE,
  total_rebounds DOUBLE,
  total_steals DOUBLE,
  total_blocks DOUBLE,
  total_turnovers DOUBLE,
  total_personal_fouls DOUBLE,
  ten_point_games HUGEINT,
  ten_rebound_games HUGEINT,
  ten_assist_games HUGEINT,
  ten_steal_games HUGEINT,
  ten_block_games HUGEINT,
  double_double_games HUGEINT,
  field_goal_pct DOUBLE,
  three_point_pct DOUBLE,
  free_throw_pct DOUBLE,
  points_per_game DOUBLE,
  assists_per_game DOUBLE,
  rebounds_per_game DOUBLE
);

-- Local DuckDB team-game fact. Grain is one row per team per canonical game, with explicit home/away and win/loss fields.
CREATE TABLE TRANSFORMED.local_team_game_facts (
  game_id BIGINT,
  game_date DATE,
  season INTEGER,
  team_id BIGINT,
  opponent_team_id BIGINT,
  is_home BOOLEAN,
  team_points DOUBLE,
  opponent_points DOUBLE,
  team_won BOOLEAN,
  team_lost BOOLEAN,
  home_team_wins INTEGER,
  game_status_text VARCHAR
);

-- Local DuckDB team-season aggregate derived only from local_team_game_facts. Grain is one row per team per source season.
CREATE TABLE TRANSFORMED.local_team_season_facts (
  team_id BIGINT,
  season INTEGER,
  first_game_date DATE,
  last_game_date DATE,
  games_played BIGINT,
  wins HUGEINT,
  losses HUGEINT,
  home_games HUGEINT,
  away_games HUGEINT,
  home_wins HUGEINT,
  away_wins HUGEINT,
  total_points DOUBLE,
  opponent_points DOUBLE,
  point_differential DOUBLE,
  win_pct DOUBLE
);

-- Source table containing raw games data.
CREATE VIEW TRANSFORMED.src_games (
  game_date_est DATE,
  games_game_id INTEGER,
  game_status_text VARCHAR,
  home_team_id INTEGER,
  visitor_team_id INTEGER,
  season INTEGER,
  team_id_home INTEGER,
  pts_home DOUBLE,
  ft_pct_home DOUBLE,
  fg3_pct_home DOUBLE,
  ast_home DOUBLE,
  reb_home DOUBLE,
  team_id_away INTEGER,
  pts_away DOUBLE,
  fg_pct_away DOUBLE,
  ft_pct_away DOUBLE,
  fg3_pct_away DOUBLE,
  ast_away DOUBLE,
  reb_away DOUBLE,
  home_team_wins INTEGER  -- Indicator of whether the home team won the game (1 for win, 0 for loss).
);

CREATE VIEW TRANSFORMED.src_games_details (
  details_game_id INTEGER,
  details_team_id INTEGER,
  team_abbreviation VARCHAR,
  team_city VARCHAR,
  player_id INTEGER,
  player_name VARCHAR,
  player_nickname VARCHAR,
  player_start_position VARCHAR,
  comment_text VARCHAR,
  games_min VARCHAR,
  fgm DOUBLE,
  fga DOUBLE,
  fg_pct DOUBLE,
  fg3m DOUBLE,
  fg3a DOUBLE,
  fg3_pct DOUBLE,
  ftm DOUBLE,
  fta DOUBLE,
  ft_pct DOUBLE,
  oreb DOUBLE,
  dreb DOUBLE,
  reb DOUBLE,
  ast DOUBLE,
  stl DOUBLE,
  blk DOUBLE,
  turnover DOUBLE,
  pf DOUBLE,
  pts DOUBLE,
  plus_minus DOUBLE
);

CREATE VIEW TRANSFORMED.src_player_information (
  TEAM_ID BIGINT,
  SEASON INTEGER,
  LEAGUE_ID VARCHAR,
  player_name VARCHAR,
  PLAYER_POSITION VARCHAR,
  HEIGHT VARCHAR,
  WEIGHT DOUBLE,
  BIRTH_DATE DATE,
  AGE DOUBLE,
  SCHOOL VARCHAR
);

CREATE VIEW TRANSFORMED.src_players (
  player_id BIGINT,
  team_id BIGINT,
  PLAYER_NAME VARCHAR,
  SEASON INTEGER
);

CREATE VIEW TRANSFORMED.src_ranking (
  league_id INTEGER,
  season_id INTEGER,
  standings_date DATE,
  conference VARCHAR,
  team VARCHAR,
  g INTEGER,
  w INTEGER,
  l INTEGER,
  w_pct DOUBLE,
  home_record VARCHAR,
  road_record VARCHAR,
  return_to_play VARCHAR
);

CREATE VIEW TRANSFORMED.src_teams (
  league_id INTEGER,
  team_id INTEGER,
  min_year INTEGER,
  max_year INTEGER,
  team_abbreviation VARCHAR,
  team_nickname VARCHAR,
  year_founded INTEGER,
  city VARCHAR,
  arena VARCHAR,
  arena_capacity INTEGER,
  team_owner VARCHAR,
  general_manager VARCHAR,
  head_coach VARCHAR,
  dleague_affiliation VARCHAR
);

CREATE VIEW TRANSFORMED.stg_player_information (
  TEAM_ID BIGINT,
  SEASON INTEGER,
  LEAGUE_ID VARCHAR,
  player_name VARCHAR,
  PLAYER_POSITION VARCHAR,
  HEIGHT_CM DECIMAL(15,2),
  WEIGHT DOUBLE,
  BIRTH_DATE DATE,
  AGE DOUBLE,
  SCHOOL VARCHAR
);

-- Local DuckDB DEV snapshot of player history.
CREATE TABLE dev.scd_raw_players (
  player_name VARCHAR,
  team_id INTEGER,
  player_id INTEGER,
  season INTEGER,
  dbt_scd_id VARCHAR,
  dbt_updated_at TIMESTAMP,
  dbt_valid_from TIMESTAMP,
  dbt_valid_to TIMESTAMP
);

-- Local DuckDB DEV snapshot of team history.
CREATE TABLE dev.scd_raw_teams (
  league_id INTEGER,
  team_id INTEGER,
  min_year INTEGER,
  max_year INTEGER,
  team_abbreviation VARCHAR,
  team_nickname VARCHAR,
  year_founded INTEGER,
  city VARCHAR,
  arena VARCHAR,
  arena_capacity INTEGER,
  team_owner VARCHAR,
  general_manager VARCHAR,
  head_coach VARCHAR,
  dleague_affiliation VARCHAR,
  dbt_scd_id VARCHAR,
  dbt_updated_at TIMESTAMP,
  dbt_valid_from TIMESTAMP,
  dbt_valid_to TIMESTAMP
);

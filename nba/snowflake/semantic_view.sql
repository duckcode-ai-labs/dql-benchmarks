-- A Snowflake semantic view over the NBA tables, to test ZLens's semantic-view import live.
-- Run as ZLENS_BENCH_LOADER (owner of NBA.TRANSFORMED); ZLens reads it as ZLENS_READER.
USE ROLE ZLENS_BENCH_LOADER;
USE WAREHOUSE ZLENS_BENCH_WH;
CREATE OR REPLACE SEMANTIC VIEW NBA.TRANSFORMED.NBA_TEAM_SEASONS
  TABLES (
    seasons AS NBA.TRANSFORMED.LOCAL_TEAM_SEASON_FACTS PRIMARY KEY (TEAM_ID, SEASON)
      COMMENT = 'One row per team per season (regular season and playoffs)',
    teams AS NBA.RAW.RAW_TEAMS PRIMARY KEY (TEAM_ID) COMMENT = 'One row per NBA team'
  )
  RELATIONSHIPS (
    season_team AS seasons (TEAM_ID) REFERENCES teams
  )
  FACTS (
    seasons.points_scored AS TOTAL_POINTS COMMENT = 'Points the team scored in the season'
  )
  DIMENSIONS (
    seasons.season AS SEASON COMMENT = 'The year the season starts',
    teams.team_name AS NICKNAME COMMENT = 'Team nickname, e.g. Warriors',
    teams.city AS CITY
  )
  METRICS (
    seasons.total_wins AS SUM(WINS) COMMENT = 'Games won',
    seasons.games_played AS SUM(GAMES_PLAYED),
    seasons.win_rate AS seasons.total_wins / NULLIF(seasons.games_played, 0) COMMENT = 'Share of games won',
    seasons.points_total AS SUM(seasons.points_scored) COMMENT = 'Points scored'
  )
  COMMENT = 'NBA team seasons: wins and points by team and season';
GRANT SELECT ON SEMANTIC VIEW NBA.TRANSFORMED.NBA_TEAM_SEASONS TO ROLE ZLENS_READER;

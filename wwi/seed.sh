#!/usr/bin/env bash
# Stand up a private Postgres holding WideWorldImporters, the way NVIDIA's
# seed_wwi.py does it: DDL 01-04, COPY every CSV, then foreign keys and views.
#
#   wwi/seed.sh start   initialise and seed on first use, then start the server
#   wwi/seed.sh stop    stop the server
#
# It listens on 127.0.0.1:55432 only, with its own data folder under work/wwi,
# so nothing here touches another Postgres on the machine. Answers run as
# wwi_reader, a role that can only read.
set -euo pipefail

# Postgres on macOS refuses to start without a valid locale in the environment.
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PGBIN=/opt/homebrew/opt/postgresql@16/bin
PGDATA="$ROOT/work/wwi/pg"
PORT=55432
DB=wideworldimporters
DATASET="$ROOT/work/wwi/dataset"
PSQL=("$PGBIN/psql" -h 127.0.0.1 -p "$PORT" -U postgres -v ON_ERROR_STOP=1 -q)

case "${1:-}" in
  stop)
    "$PGBIN/pg_ctl" -D "$PGDATA" stop -m fast
    exit 0
    ;;
  start) ;;
  *)
    echo "usage: wwi/seed.sh start|stop" >&2
    exit 2
    ;;
esac

first_run=false
if [ ! -d "$PGDATA" ]; then
  "$PGBIN/initdb" -D "$PGDATA" -U postgres --auth=trust --encoding=UTF8 --locale=C >/dev/null
  first_run=true
fi

"$PGBIN/pg_ctl" -D "$PGDATA" -l "$ROOT/work/wwi/pg.log" -w \
  -o "-p $PORT -c listen_addresses=127.0.0.1 -c unix_socket_directories=$PGDATA" start

if [ "$first_run" = false ]; then
  exit 0
fi

"${PSQL[@]}" -d postgres -c "CREATE DATABASE $DB"

for file in 01_schemas 02_sequences 03_tables 04_indexes; do
  "${PSQL[@]}" -d "$DB" -f "$DATASET/ddl/$file.sql"
done

total=0
for csv in "$DATASET"/data/*.csv; do
  name="$(basename "$csv" .csv)"
  table="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')"
  "${PSQL[@]}" -d "$DB" -c "\\copy $table FROM '$csv' WITH (FORMAT csv, HEADER true, NULL '\\N')"
  rows="$("${PSQL[@]}" -d "$DB" -tAc "SELECT count(*) FROM $table")"
  total=$((total + rows))
done
echo "loaded $total rows"

for file in 05_fkeys 06_views; do
  "${PSQL[@]}" -d "$DB" -f "$DATASET/ddl/$file.sql"
done

"${PSQL[@]}" -d "$DB" <<'SQL'
CREATE ROLE wwi_reader LOGIN;
ALTER ROLE wwi_reader SET default_transaction_read_only = on;
DO $$
DECLARE s text;
BEGIN
  FOR s IN SELECT nspname FROM pg_namespace WHERE nspname !~ '^(pg_|information_schema)' LOOP
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO wwi_reader', s);
    EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO wwi_reader', s);
  END LOOP;
END $$;
ANALYZE;
SQL
echo "seeded $DB on 127.0.0.1:$PORT"

-- MetricFlow time spine for the ACME insurance business layer (DuckDB).
-- One row per day over a range wide enough for every policy term, coverage
-- period, claim and occurrence date in the warehouse.
{{ config(materialized='table') }}

select cast(range as date) as date_day
from range(date '2010-01-01', date '2031-01-01', interval 1 day)

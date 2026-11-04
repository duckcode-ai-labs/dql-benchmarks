# Postcard benchmark: gold policy

What the business's words mean in this data, decided before any gold SQL was written.
Every count below was run read-only on `work/postcard/source/datamart.duckdb`
(duckdb 1.5.6). Sources cited are in
`/Users/Kranthi_1/DuckCode-DQL/blind-second-project/postcard-company-datamart`
(`models/` means `postcard_company/models/`).

The database is a clean dbt build of that project. The generator's window ends
on 2026-10-26, and the build loaded 300,000 sales. There is no semantic layer:
`target/semantic_manifest.json` has no models or metrics. Gold reads the core
schema `postcard_company_core` unless a raw or staging table holds exactly the
same rows.

## 1. What a sale is

- **One sale is one row of `fact_sales`.** Each row is one transaction: one product
  line with a quantity. There is no order header grouping several lines, so
  "sale", "order" and "transaction" all mean one row.
  - `fact_sales` has 300,000 rows: 100,000 direct sales and 4 × 50,000 reseller
    sales. Sources: `models/core/fact/fact_sales.sql`,
    `models/staging/staging_transactions.sql`, and `generate_main` /
    `generate_type1_reseller_data` / `generate_type2_reseller_data` in
    `generator/generate.py`.
- **Transaction ids are unique across all three feeds.** The generator draws them
  from one shared counter (`transaction_id_counter`), and `models/schema.yml`
  tests `staging_transactions.transaction_id` as unique. Checked: 300,000
  distinct ids.
- **"Postcards", "cards" or "units" sold means `SUM(qty)`, not a row count.**
  In 2025 that is 499,284 cards over 149,716 sales.
- **Quantity per sale** is 1 to 5 on direct sales and 1 to 6 on reseller sales
  (`randrange` in `generate.py`; checked).

## 2. The amount of a sale

- **Revenue is `SUM(total_amount)`.** `total_amount` is the gross line value,
  quantity × list price (`schema.yml`, `fact_sales.total_amount`).
  - Checked: `total_amount = qty × product_price` on all 300,000 rows.
  - `fact_sales.product_price` equals `dim_product.product_price` on every row,
    so there is no price history.
- **Revenue is gross.** Commission is not taken off unless the question asks for
  what we keep (see section 3).
- **There is one currency and no conversion.** The data has no currency column.
- **Amounts carry floating-point noise.** They are DOUBLE (for example
  `6.8999999999999995`). Gold rounds money to 2 decimals when the question asks.
- **`raw_transactions.amount` is already the line total**, not a unit price.
  Multiplying it by `qty` overstates 2025 direct revenue: 1,627,857.20 instead of
  442,931.60.

## 3. Direct and reseller sales; commission

- **Who made the sale is `fact_sales.sales_agent_key`.**
  - Key 0 is the company's own direct sales. `dim_sales_agent.sql` adds this as a
    synthetic row, `'Direct Sales'`, with a NULL rate.
  - Keys 1001–1004 are the four resellers.
  - `dim_sales_agent` therefore has 5 rows, but **"resellers" means the 4 rows with
    key ≠ 0.**
- **Commission rates:**

  | Reseller | Key | Rate |
  |---|---|---|
  | Imaginary Street Press Company | 1001 | 0.15 |
  | European Example Press Corporation | 1002 | 0.17 |
  | Scandinavian Legendary Printing Company | 1003 | 0.14 |
  | Mediterranean Postcard Press Association | 1004 | 0.16 |

  Raw, staging and core agree on these rates.
- **`commissionpaid` is `commission_pct × total_amount` on reseller sales and NULL
  on direct sales.** Sources: `schema.yml`; test
  `tests/commissionpct_null_only_for_direct_sales.sql`. Checked: NULL on exactly
  the 100,000 direct rows.
- **What we keep after commissions** (net revenue) is
  `SUM(total_amount) − SUM(COALESCE(commissionpaid, 0))`. For 2025 that is
  1,314,829.13.
  - `SUM(total_amount − commissionpaid)` gives 871,897.53, because the NULLs drop
    every direct sale.
- **"Partner" means a reseller.**

## 4. What a customer is

- **A customer is a `dim_customer.customer_key`.** `schema.yml` documents the key:
  "Direct customers key off their source customer_id; reseller customers have no
  stable identifier, so they key off (reseller_id, email)". Source:
  `models/staging/staging_customers.sql`.
- **`dim_customer` has 280,063 rows:** 100,000 direct customers on file plus
  180,063 reseller customers.
  - 36,793 of the direct customers on file never bought; all of them are direct.
  - Every reseller customer bought, because reseller customers exist only from
    their sales rows.
  - **Customers who bought** = `COUNT(DISTINCT customer_key)` over `fact_sales` =
    **243,270**.
- **Direct customers are identified by `customer_id`.** "Customer number" means
  `original_customer_id`.
  - Emails are not a person key: the 100,000 direct customers share 83,638
    distinct emails.
  - 63,207 direct customers bought. Customers 0 and 1 never did, because the
    generator draws buyers with `randrange(1, 100000)`.
- **A reseller customer is one email at one reseller**, however many sale rows
  carry that email.
  - The same email at two resellers counts as two customers.
  - Example: reseller 1001 in 2025 has 25,144 sale rows and 25,144 distinct
    phone numbers, but 23,723 customers.
  - Counting distinct emails across everything (187,405 buyers) is not the
    data mart's definition and is not used.
- **Reseller customers' names, addresses and countries are `MIN()` over that
  email's rows** (`staging_customers.sql`). They are not reliable per person, so
  gold asks customer-location questions about direct customers only.
- **A new customer in a period** is a `customer_key` whose first sale falls in that
  period. Sales begin on 2024-10-25, so "first sale in the data" is the first
  sale.
- **A repeat customer** is one with more than one sale. 31 customers have 2 or more
  sales all on one day; they count, because each sale is a separate purchase.
- **Names repeat** ("Michael Smith" is 37 direct customers). Gold groups by
  customer key or number, never by name.

## 5. Products and geography

- **There are 500 products** (`dim_product`, one per `product_id`).
- **`product_name` reads `"<size> - <city> - <catchphrase>"`.** The postcard size
  (4x6, 4.25x6, 5x7, 5.5x8.5, 6x9, 6x11) exists only as that prefix
  (`PRODUCT_FORMATS` in `generate.py`). Checked: every name splits into one of the
  6 sizes.
- **`dim_geography` is the city a postcard depicts, not where the buyer lives.**
  - It comes from `seeds/geography.csv`: 100 cities, 27 countries, 5 regions.
  - `fact_sales.geography_key` is the product's geography: `staging_products.sql`
    joins the product's city to the seed, and the sales staging models take
    `p.geography_key`.
  - So "postcards of German cities" means `dim_geography.country_name = 'Germany'`
    (2025: 164,972.80).
- **Where a customer lives is `dim_customer.customer_city` / `customer_country`.**
  These are Faker free text covering the whole world. In 2025, customers living
  in Germany spent 6,710.20.
- **City names are in local form with the English name in brackets**, for example
  `'Wien (Vienna)'` and `'Moskva (Moscow)'`.
  - Two names have a **trailing space**: `'Donetsk '` and `'Mykolaiv '`. The space
    is in the generator's `CITIES` list, the seed, `raw_products.city`, the
    resellers' `Series City`, and the product names.
  - Matching on `'Donetsk'` finds nothing, so gold matches with `TRIM`.
- **Regions follow the seed.** For example Zagreb (Croatia) is in Eastern Europe,
  and every Russian city is in Eastern Europe.

## 6. Dates and periods

- **The sale date is `fact_sales.bought_date_key`** (YYYYMMDD integer), which joins
  to `dim_date.date_key`. All 300,000 rows join.
- **Sales run from 2024-10-25 to 2026-10-26**: 732 days, and every day has sales.
  - 2025 is the only full calendar year.
  - October 2024 starts on the 25th and October 2026 ends on the 26th.
  - Years, quarters and months are calendar ones; there is no fiscal calendar.
- **"So far" and "to date" mean up to the last sale, 2026-10-26**, not the wall
  clock.
  - A year-to-date comparison uses the same dates a year earlier
    (2025-01-01 to 2025-10-26): +0.2%.
  - Comparing all of 2026 with all of 2025 gives −18.1%.
- **`dim_date` is a calendar spine** from 2010-01-01 to 2035-12-31 (9,496 rows;
  `dim_date.sql`, `calendar_start` / `calendar_end` vars). It is not a list of
  selling days.
- **`day_of_week` is DuckDB `DAYOFWEEK`: Sunday = 0 … Saturday = 6.**
  - `iso_day_of_week` is Monday = 1 … Sunday = 7.
  - Weekend means Saturday and Sunday: `day_name` or `iso_day_of_week IN (6, 7)`.
  - `day_of_week IN (6, 7)` catches Saturday only.
- **`week_key` is the ISO `YEARWEEK`**, so 2024-12-30 falls in week 202501. Gold
  asks no week questions.

## 7. What the raw and staging layers get wrong, and what they don't

- **Values agree across layers.** Raw and staging hold the same values as core for
  every row they cover.
  - Checked over all 300,000 sales, 0 mismatches between each raw feed and
    `fact_sales` on amount, quantity and date.
  - `staging_customers` = `dim_customer`.
  - `raw_resellers` = `staging_resellers` = `dim_sales_agent`, except the Direct
    Sales row.
- **There are no repeated rows and no type-2 history.**
  - `raw_products` has 500 distinct `product_id`, `raw_resellers` 4 and
    `raw_customers` 100,000 distinct ids.
  - The staging `QUALIFY ROW_NUMBER()` dedupes (products, resellers) remove
    nothing.
  - Nothing is versioned.
- **Coverage is where the layers differ.** Each raw or staging feed table holds only
  part of the business:

  | Table(s) | Holds |
  |---|---|
  | `raw_transactions`, `staging_transactions_main` | direct sales only (2025: 149,742 of 499,284 cards) |
  | `*_reseller_type1_sales` | resellers 1001–1002 only |
  | `*_reseller_type2_sales` | resellers 1003–1004 only |
  | `raw_customers` | direct customers only, including the 36,793 who never bought |
  | `staging_transactions` | all 300,000 sales, row for row the same as `fact_sales` |

- **The raw sales feeds carry no commission.** Commission comes from the reseller's
  rate.
- **The reseller feeds repeat the customer on every sale row.** Only the core's
  `(reseller, email)` key turns those rows into customers.
- **Rule:** any question about all sales reads `fact_sales` (or
  `staging_transactions`). A per-feed table is acceptable only when the question
  is limited to that feed's sellers.

## 8. `needs` in `questions.json`

Each inner list is a group of alternative tables, written `schema.table` in lower
case. The answer must read at least one table from every group. Tables that
would give a wrong answer are left out of the group. For example, for a 2025
total over all sales, the sales group is `fact_sales` / `staging_transactions`
only.

A date dimension is never required: `bought_date_key` and the raw date strings
already carry the date.

-- budget_guard.sql
-- Run before every force_entry call
-- Returns: status, remaining_usd, block_trading flag
--
-- Usage:
--   duckdb ~/kestrel/signals.duckdb -init budget_guard.sql -noheader -csv
--   or in Python: con.execute(open("budget_guard.sql").read()).fetchone()

WITH spend AS (
    SELECT
        COALESCE(SUM(amount_usd), 0) AS total_spent,
        COALESCE(SUM(CASE WHEN engine = 'freqtrade' THEN amount_usd END), 0) AS ft_spent
    FROM trade_log
    WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
)
SELECT
    ROUND(total_spent, 2) AS total_spent_usd,
    ROUND(ft_spent, 2) AS freqtrade_spent_usd,
    ROUND(50.0 - total_spent, 2) AS remaining_usd,
    10.0 AS per_trade_cap,
    5.0 AS floor_usd,
    CASE
        WHEN (50.0 - total_spent) < 5.0  THEN 'red'
        WHEN (50.0 - total_spent) < 25.0 THEN 'yellow'
        ELSE 'green'
    END AS status,
    CASE
        WHEN (50.0 - total_spent) < 5.0  THEN TRUE
        ELSE FALSE
    END AS block_trading
FROM spend;

-- Short Python version:
-- con.execute("""
--     SELECT (50.0 - COALESCE(SUM(amount_usd), 0)) >= 5.0 AS ok
--     FROM trade_log
--     WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
-- """).fetchone()[0]
-- ============================================================================
-- budget_guard.sql
--
-- DuckDB budget guard query for the Striker dual execution pipeline.
--
-- Returns the daily budget status for trading engines based on the trade_log.
-- Used by both Freqtrade and MMR supervisors to enforce per-engine spending caps.
--
-- Output columns:
--   status       | 'green'  — spend < 80% of daily cap
--                | 'yellow' — spend >= 80% but < 100% of cap
--                | 'red'    — spend >= 100% of cap (falls back to floor)
--   remaining_usd| Dollar amount remaining before hitting the effective cap
--   block_trading| TRUE when budget is exhausted (red), FALSE otherwise
-- ============================================================================

WITH daily_spend AS (
    SELECT
        engine,
        COALESCE(SUM(amount), 0.0) AS total_spend,
        COUNT(*) AS trade_count
    FROM trade_log
    WHERE date_trunc('day', executed_at) = date_trunc('day', NOW())
    GROUP BY engine
),
budget AS (
    SELECT
        d.engine,
        d.total_spend,
        d.trade_count,
        50.0 AS daily_cap,
        5.0  AS degradation_floor,
        CASE
            WHEN d.total_spend < 50.0 THEN 50.0
            ELSE 5.0
        END AS effective_cap
    FROM daily_spend d
)
SELECT
    engine,
    CASE
        WHEN total_spend >= effective_cap THEN 'red'
        WHEN total_spend >= (effective_cap * 0.8) THEN 'yellow'
        ELSE 'green'
    END AS status,
    ROUND(effective_cap - total_spend, 2) AS remaining_usd,
    CASE
        WHEN total_spend >= effective_cap THEN TRUE
        ELSE FALSE
    END AS block_trading,
    ROUND(total_spend, 2) AS spent_today,
    trade_count
FROM budget
ORDER BY engine;
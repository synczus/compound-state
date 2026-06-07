-- Ranked Signal Queue — DuckDB Scoring Query v0.1
-- Perplexity Round 2: ranks all signals by edge_score for Synapse dashboard & alerts
-- Tier multipliers: lead_indicator ×1.15, catalyst_confirmation ×1.00, narrative_formation ×0.90
-- Bluechip boost: BTC/ETH/SOL ×1.10
-- Decay: half-life 30min lead, 120min catalyst, 720min narrative
-- Cross-source boost: 2+ sources same asset/15min = +15% per extra source (capped +35%)

WITH scored AS (
  SELECT
    ss.*,
    sa.agreement_boost,
    sf.wolf_rate,
    sf.false_positive_penalty,
    CASE
      WHEN ss.tier = 'lead_indicator' THEN 1.15
      WHEN ss.tier = 'narrative_formation' THEN 0.90
      ELSE 1.00
    END AS tier_mult,
    CASE
      WHEN ss.asset_symbol IN ('BTC', 'ETH', 'SOL') THEN 1.10
      ELSE 1.00
    END AS bluechip_mult
  FROM signal_scores ss
  LEFT JOIN source_agreement sa
    ON ss.signal_id = sa.signal_id
    AND ss.asset_symbol = sa.asset_symbol
    AND date_trunc('minute', ss.event_ts) = sa.bucket_minute
  LEFT JOIN source_feedback sf
    ON ss.source_id = sf.source_id
)
SELECT
  signal_id,
  source_id,
  asset_symbol,
  event_type,
  event_ts,
  tier,
  ROUND(
    source_prior *
    reported_confidence *
    asset_relevance *
    novelty *
    recency_weight *
    COALESCE(cross_source_boost, 1.0) *
    COALESCE(false_positive_penalty, 1.0) *
    tier_mult *
    bluechip_mult
  , 4) AS edge_score,
  ROUND(recency_weight, 4) AS recency,
  ROUND(COALESCE(cross_source_boost, 1.0), 3) AS boost,
  rationale
FROM scored
ORDER BY edge_score DESC, event_ts DESC
LIMIT 20;
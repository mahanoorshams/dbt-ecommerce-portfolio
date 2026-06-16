-- Singular test: every rate that is expressed as a proportion must sit between
-- 0 and 1. If any row fails this, a downstream chart or headline figure would
-- be wrong, so it is worth catching at build time. The test passes when it
-- returns zero rows.

select 'category return_rate' as failing_metric, category as grain, return_rate as value
from {{ ref('mart_category_performance') }}
where return_rate < 0 or return_rate > 1

union all

select 'category gross_margin_pct', category, gross_margin_pct
from {{ ref('mart_category_performance') }}
where gross_margin_pct < -1 or gross_margin_pct > 1

union all

select 'cohort repeat_purchase_rate', cast(cohort_month as string), repeat_purchase_rate
from {{ ref('mart_customer_retention') }}
where repeat_purchase_rate < 0 or repeat_purchase_rate > 1

union all

select 'channel repeat_purchase_rate', traffic_source, repeat_purchase_rate
from {{ ref('mart_channel_performance') }}
where repeat_purchase_rate < 0 or repeat_purchase_rate > 1

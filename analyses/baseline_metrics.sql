
-- ============================================================
-- Baseline Metrics: Checkout Free Shipping Banner A/B Test
-- Analyst: Mahanoor Shams
-- Date: June 2026
-- Purpose: Establish baseline figures for experiment design
--          and power calculation before the test window opens.
-- Source: bigquery-public-data.thelook_ecommerce
-- ============================================================
 
 
-- Query 1: Average order value and standard deviation
-- Used to calculate minimum detectable effect and sample size.
-- Result: baseline_aov = $86.03, aov_stddev = $93.98, order_count = 31,144
 
select
    round(avg(order_value), 2)    as baseline_aov,
    round(stddev(order_value), 2) as aov_stddev,
    count(*)                       as order_count
from (
    select
        order_id,
        sum(sale_price) as order_value
    from `bigquery-public-data.thelook_ecommerce.order_items`
    where status = 'Complete'
    group by order_id
);
 
 
-- Query 2: Baseline return rate
-- Used as the guardrail metric. If treatment return rate exceeds
-- control by more than 3 percentage points, pause the experiment.
-- Result: baseline_return_rate = 0.286 (28.6%), total_orders = 43,617
 
select
    round(
        countif(status = 'Returned') / count(*),
        4
    )        as baseline_return_rate,
    count(*) as total_orders
from `bigquery-public-data.thelook_ecommerce.orders`
where status in ('Complete', 'Returned');
 
 
-- Query 3: Average daily completed order volume
-- Used to estimate test duration: days = n_per_variant / (avg_daily_orders * 0.5)
-- Result: avg_daily_orders = 12.39
-- At this volume, a 5% AOV lift would require ~1,210 days to detect.
-- The simulation approach resolves this by using the full historical dataset.
 
select
    avg(daily_orders) as avg_daily_orders
from (
    select
        date(created_at)        as order_date,
        count(distinct order_id) as daily_orders
    from `bigquery-public-data.thelook_ecommerce.orders`
    where status = 'Complete'
    group by 1
);
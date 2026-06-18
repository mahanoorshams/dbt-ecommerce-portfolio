# Experiment Design: Checkout Free Shipping Threshold Banner

**Project:** thelook_ecommerce A/B Test  
**Dataset:** `dbt-portfolio-498511.dbt_analytics`  
**Analyst:** Mahanoor Shams  
**Status:** Draft  
**Date:** June 2026  

---

## Background

Checkout abandonment is one of the biggest revenue leaks in e-commerce. One of the most common nudges used to reduce it, and to lift basket size, is a dynamic banner showing the customer how close they are to qualifying for free shipping. This experiment tests whether adding a free shipping threshold banner to the checkout page raises average order value without causing customers to game the threshold by buying extra items they then return.

The dataset is `thelook_ecommerce`, a public BigQuery dataset simulating a fashion retailer. Because the dataset is static, this experiment follows a reconstruction design: the banner variant is simulated using a hash of `user_id`, and the resulting assignment is joined to actual order data. The analysis treats this as if the experiment were run prospectively.

---

## Hypothesis

Displaying a "Free shipping on orders over $50" banner at checkout will increase average order value compared to the standard checkout experience, because customers will add additional items to qualify for free shipping rather than pay a shipping fee.

We expect no meaningful increase in return rate. If return rate rises significantly in the treatment group, it would suggest customers are purchasing extra items they do not intend to keep, which would undermine the value of any AOV lift.

---

## Experiment Setup

| Parameter | Detail |
|---|---|
| Control | Standard checkout page, no shipping banner |
| Treatment | Checkout page with "Free shipping on orders over $50" banner |
| Assignment method | MD5 hash of `user_id`, split 50/50 using modulo 2 |
| Assignment unit | User, not session. Each user sees the same variant for the full test window |
| Scope | All users who place at least one order during the test period |

Assignment is handled by the dbt staging model `stg_experiment_assignments`. Any user who places more than one order during the test window is always assigned to the same variant, preventing crossover contamination.

---

## Metrics

### Primary Metric: Average Order Value (AOV)

**Definition:** Total sale price across all items in a completed order, divided by the number of completed orders, grouped by variant.

**Direction:** Increase. The treatment group should produce a higher AOV than control.

Run this query against the source data before the test begins to establish the baseline:

```sql
select
    round(avg(order_value), 2) as baseline_aov,
    round(stddev(order_value), 2)  as aov_stddev,
    count(*)                        as order_count
from (
    select
        order_id,
        sum(sale_price) as order_value
    from `bigquery-public-data.thelook_ecommerce.order_items`
    where status = 'Complete'
    group by order_id
)
```

### Guardrail Metric: Return Rate

**Definition:** The proportion of completed orders that are subsequently returned, grouped by variant.

**Direction:** No meaningful increase. If treatment return rate exceeds control by more than 3 percentage points, the experiment should be reviewed before any rollout decision is made.

Run this query to establish the baseline return rate:

```sql
select
    round(
        countif(status = 'Returned') / count(*),
        4
    ) as baseline_return_rate,
    count(*) as total_orders
from `bigquery-public-data.thelook_ecommerce.orders`
where status in ('Complete', 'Returned')
```

---

## Statistical Plan

### Parameters

| Parameter | Value | Rationale |
|---|---|---|
| Significance level (alpha) | 0.05 | Standard threshold. One in 20 chance of a false positive |
| Statistical power (1 minus beta) | 0.80 | 80% chance of detecting a real effect if one exists |
| Test type | Two-tailed | Testing for any AOV difference, not assuming direction in advance |
| Statistical test | Welch t-test | Does not assume equal variance between variants, which is appropriate for order value data |

### Minimum Detectable Effect

A 5% relative lift in AOV is the minimum that would justify a full rollout. Lifts smaller than this would likely be outweighed by the ongoing cost of maintaining the banner in production.

Using baseline estimates from the queries above (update these figures with actual query results before finalising):

| Estimate | Value | Source |
|---|---|---|
| Baseline AOV | ~$82.50 | Baseline SQL query |
| MDE at 5% relative lift | ~$4.13 (absolute) | 82.50 × 0.05 |
| Standard deviation of order value | ~$48.30 | Baseline SQL query |

### Sample Size Calculation

The formula for a two-sample t-test with equal group sizes:

```
n = 2σ² × (z_α/2 + z_β)² / δ²
```

Where:

- `σ` = standard deviation of AOV
- `z_α/2` = 1.96 (alpha = 0.05, two-tailed)
- `z_β` = 0.84 (power = 0.80)
- `δ` = minimum detectable effect in absolute terms

Substituting the baseline estimates:

```
n = 2 × (48.30²) × (1.96 + 0.84)² / (4.13²)
n = 2 × 2,332.89 × 7.84 / 17.06
n ≈ 2,144 per variant
n ≈ 4,288 total
```

Approximately 2,144 completed orders per variant are needed to detect a 5% AOV lift with 80% power at the 5% significance level.

Use this Python snippet to recalculate with the actual baseline figures once the SQL queries have been run:

```python
from statsmodels.stats.power import TTestIndPower
import numpy as np

baseline_aov  = 82.50   # update with actual query result
aov_stddev    = 48.30   # update with actual query result
mde_relative  = 0.05
alpha         = 0.05
power         = 0.80

mde_absolute  = baseline_aov * mde_relative
cohens_d      = mde_absolute / aov_stddev

analysis      = TTestIndPower()
n_per_variant = analysis.solve_power(
    effect_size = cohens_d,
    alpha       = alpha,
    power       = power,
    alternative = 'two-sided'
)

print(f"MDE (absolute):     ${mde_absolute:.2f}")
print(f"Cohen's d:          {cohens_d:.4f}")
print(f"Sample size needed: {int(np.ceil(n_per_variant))} per variant")
print(f"Total sample size:  {int(np.ceil(n_per_variant)) * 2}")
```

---

## Recommended Test Duration

To convert the sample size requirement into a calendar duration, query the average daily completed order volume from the source data:

```sql
select
    avg(daily_orders) as avg_daily_orders
from (
    select
        date(created_at) as order_date,
        count(distinct order_id) as daily_orders
    from `bigquery-public-data.thelook_ecommerce.orders`
    where status = 'Complete'
    group by 1
)
```

Then apply this formula:

```
days_required = n_per_variant / (avg_daily_orders × 0.50)
```

The 0.50 accounts for the 50/50 split: only half of all daily orders will land in any one variant. Round up to the nearest week and add at least one additional week as a buffer.

**Minimum duration regardless of sample size:** 4 weeks.

Running for less than 4 weeks risks capturing an unrepresentative mix of weekdays and weekends, and may not allow enough time for any novelty effect from the banner to settle. Even if the required sample size is reached in week two, the test should continue to the 4-week mark.

---

## Success and Failure Criteria

| Outcome | Criteria | Decision |
|---|---|---|
| Clear win | AOV lift is statistically significant (p < 0.05) and at least 5% relative | Roll out to 100% of users |
| Inconclusive | No statistically significant AOV difference | Extend the test or investigate banner visibility |
| Guardrail breach | Treatment return rate exceeds control by more than 3 percentage points | Pause and investigate before making any rollout decision |
| Clear loss | Treatment AOV is significantly lower than control | Do not roll out. Investigate whether the banner created friction or distracted from conversion |

---

## Risks and Assumptions

**Novelty effect.** Users may interact with the banner differently in the first few days simply because it is unfamiliar. Running for at least 4 weeks mitigates this, as the effect tends to diminish over time.

**Assignment leakage.** A user could technically be assigned to both variants if they log in from different accounts or clear cookies. The hash approach on `user_id` reduces but does not eliminate this. For this portfolio project, leakage is assumed to be negligible.

**Seasonality.** The thelook_ecommerce dataset spans several years. The test window used in the simulation should avoid any atypically high or low-traffic periods, such as a simulated holiday peak, to avoid confounding the results.

**Return rate lag.** Returns may take days or weeks to appear in the data after a purchase. The return rate analysis should be run with a trailing observation window of at least 30 days after the test closes, to capture the majority of returns before drawing conclusions.

**Shipping threshold design.** This design assumes a flat $50 threshold and a single static banner. A more sophisticated version of this experiment might test a dynamic banner showing the customer their specific remaining amount to qualify. That is out of scope here but noted as a natural next iteration.

---

*This document was written before the simulation data was generated and serves as the pre-registered design for the experiment analysis.*

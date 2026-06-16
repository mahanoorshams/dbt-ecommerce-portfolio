-- Business question: do customers come back? Grouped by the month a customer
-- placed their first order (their acquisition cohort), what share go on to
-- order again?
--
-- Grain: one row per monthly acquisition cohort.
-- A "repeat customer" is any user with two or more distinct orders.

with orders as (
    select
        user_id,
        order_id,
        order_created_at
    from {{ ref('dim_orders') }}
    where status != 'Cancelled'
),

customer_orders as (
    select
        user_id,
        count(distinct order_id)            as lifetime_orders,
        min(order_created_at)               as first_order_at
    from orders
    group by user_id
),

cohorts as (
    select
        date_trunc(date(first_order_at), month) as cohort_month,
        user_id,
        case when lifetime_orders >= 2 then 1 else 0 end as is_repeat_customer
    from customer_orders
)

select
    cohort_month,
    count(*)                                                 as new_customers,
    sum(is_repeat_customer)                                  as repeat_customers,
    round(safe_divide(sum(is_repeat_customer), count(*)), 4) as repeat_purchase_rate
from cohorts
group by cohort_month
order by cohort_month

-- Business question: which acquisition channel brings the most valuable and
-- the stickiest customers? Spend follows the channel that wins on revenue per
-- customer and repeat rate, not just raw sign-up volume.
--
-- Grain: one row per traffic_source (acquisition channel).

with users as (
    select
        user_id,
        traffic_source
    from {{ ref('dim_users') }}
),

orders as (
    select
        user_id,
        order_id
    from {{ ref('dim_orders') }}
    where status != 'Cancelled'
),

order_items as (
    select
        oi.user_id,
        oi.sale_price
    from {{ ref('fct_order_items') }} oi
    where oi.status != 'Cancelled'
),

orders_per_user as (
    select
        user_id,
        count(distinct order_id) as lifetime_orders
    from orders
    group by user_id
),

revenue_per_user as (
    select
        user_id,
        sum(sale_price) as lifetime_revenue
    from order_items
    group by user_id
),

user_level as (
    select
        u.user_id,
        u.traffic_source,
        coalesce(o.lifetime_orders, 0)   as lifetime_orders,
        coalesce(r.lifetime_revenue, 0)  as lifetime_revenue,
        case when o.lifetime_orders >= 2 then 1 else 0 end as is_repeat_customer
    from users u
    left join orders_per_user o on u.user_id = o.user_id
    left join revenue_per_user r on u.user_id = r.user_id
)

select
    traffic_source,
    count(*)                                                  as customers,
    sum(lifetime_orders)                                      as total_orders,
    round(sum(lifetime_revenue), 2)                           as total_revenue,
    round(safe_divide(sum(lifetime_revenue), count(*)), 2)    as revenue_per_customer,
    round(safe_divide(sum(lifetime_orders), count(*)), 2)     as orders_per_customer,
    round(safe_divide(sum(is_repeat_customer), count(*)), 4)  as repeat_purchase_rate
from user_level
group by traffic_source
order by total_revenue desc

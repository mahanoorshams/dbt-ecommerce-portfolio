-- Business question: which product categories actually make money once we
-- account for cost of goods and returns, not just headline revenue?
--
-- Grain: one row per product category.
-- Built on fct_order_items (sale price, returns) joined to dim_products (cost).
-- Cancelled items are excluded from sold revenue; a returned item is one with
-- a non-null returned_at.

with order_items as (
    select * from {{ ref('fct_order_items') }}
),

products as (
    select * from {{ ref('dim_products') }}
),

joined as (
    select
        p.category,
        p.department,
        oi.order_item_id,
        oi.sale_price,
        p.cost,
        case when oi.status = 'Cancelled' then 1 else 0 end as is_cancelled,
        case when oi.returned_at is not null then 1 else 0 end as is_returned
    from order_items oi
    inner join products p
        on oi.product_id = p.product_id
)

select
    category,
    department,
    count(*)                                              as items_ordered,
    sum(case when is_cancelled = 0 then 1 else 0 end)     as items_sold,
    sum(is_returned)                                      as items_returned,

    -- revenue only counts items that were not cancelled
    round(sum(case when is_cancelled = 0 then sale_price else 0 end), 2)
                                                          as gross_revenue,
    round(sum(case when is_cancelled = 0 then cost else 0 end), 2)
                                                          as cost_of_goods,
    round(sum(case when is_cancelled = 0 then sale_price - cost else 0 end), 2)
                                                          as gross_margin,

    -- margin % and return rate as decimals for easy formatting downstream
    round(
        safe_divide(
            sum(case when is_cancelled = 0 then sale_price - cost else 0 end),
            sum(case when is_cancelled = 0 then sale_price else 0 end)
        ), 4
    )                                                     as gross_margin_pct,
    round(
        safe_divide(sum(is_returned), sum(case when is_cancelled = 0 then 1 else 0 end)), 4
    )                                                     as return_rate

from joined
group by category, department
order by gross_margin desc

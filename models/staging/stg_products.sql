with source as (
    select * from {{ source('thelook_ecommerce', 'products') }}
),

renamed as (
    select
        id              as product_id,
        name            as product_name,
        brand,
        category,
        department,
        cost,
        retail_price
    from source
)

select * from renamed
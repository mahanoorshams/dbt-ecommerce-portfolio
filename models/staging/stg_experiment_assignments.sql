{{
    config(
        materialized = 'view'
    )
}}

/*
    Assigns every user in thelook_ecommerce to either the control or treatment
    variant using a deterministic hash of their user_id.

    FARM_FINGERPRINT is used rather than MD5 because MD5 returns BYTES in
    BigQuery Standard SQL and cannot be used directly with MOD. FARM_FINGERPRINT
    returns INT64 and produces an equivalent even distribution across both
    variants. The experiment_design.md should be updated to reflect this.

    Any user who places more than one order during the test window will always
    be assigned to the same variant, preventing crossover contamination.
*/

with source as (

    select
        id         as user_id,
        created_at as user_created_at,
        country,
        age,
        gender
    from {{ source('thelook_ecommerce', 'users') }}

),

assigned as (

    select
        user_id,
        user_created_at,
        country,
        age,
        gender,

        -- Deterministic 50/50 assignment keyed on user_id.
        -- MOD(ABS(hash), 2) produces 0 or 1 with an even distribution.
        case
            when mod(abs(farm_fingerprint(cast(user_id as string))), 2) = 0
                then 'control'
            else 'treatment'
        end as variant,

        -- Expose the raw modulo value so it is easy to audit the 50/50 split.
        mod(abs(farm_fingerprint(cast(user_id as string))), 2) as variant_key

    from source

)

select * from assigned

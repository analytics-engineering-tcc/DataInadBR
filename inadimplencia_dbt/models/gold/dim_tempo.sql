{{ config(materialized='table', schema='gold') }}

with datas as (
    select distinct mes_ref
    from {{ ref('stg_bcb_inadimplencia') }}
)

select
    mes_ref                             as data_ref,
    extract(year from mes_ref)::int     as ano,
    extract(month from mes_ref)::int    as mes,
    to_char(mes_ref, 'TMMonth')         as nome_mes,
    extract(quarter from mes_ref)::int  as trimestre,
    'T' || extract(quarter from mes_ref)::int || '/' || extract(year from mes_ref)::int as trimestre_label
from datas
order by mes_ref

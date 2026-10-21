{{ config(materialized='table', schema='gold') }}

with inadimplencia as (
    select
        mes_ref,
        serie,
        descricao,
        avg(valor) as valor
    from {{ ref('stg_bcb_inadimplencia') }}
    group by mes_ref, serie, descricao
),

desocupacao as (
    select
        mes_ref,
        avg(valor) as taxa_desocupacao
    from {{ ref('stg_ibge_indicadores') }}
    where indicador = 'Taxa de desocupacao'
    group by mes_ref
),

ipca as (
    select
        mes_ref,
        avg(valor) as ipca_variacao
    from {{ ref('stg_ibge_indicadores') }}
    where indicador = 'IPCA variacao mensal'
    group by mes_ref
),

pib as (
    select
        mes_ref,
        avg(valor) as pib_mensal
    from {{ ref('stg_ipeadata_indicadores') }}
    where indicador = 'PIB mensal'
    group by mes_ref
),

rendimento as (
    select
        mes_ref,
        avg(valor) as rendimento_real
    from {{ ref('stg_ipeadata_indicadores') }}
    where indicador = 'Rendimento medio real habitual'
    group by mes_ref
)

select
    i.mes_ref,
    i.serie,
    i.descricao,
    i.valor                 as valor_indicador,
    d.taxa_desocupacao,
    ip.ipca_variacao,
    p.pib_mensal,
    r.rendimento_real
from inadimplencia i
left join desocupacao d  on i.mes_ref = d.mes_ref
left join ipca ip        on i.mes_ref = ip.mes_ref
left join pib p          on i.mes_ref = p.mes_ref
left join rendimento r   on i.mes_ref = r.mes_ref
order by i.mes_ref, i.serie

with fonte as (
    select * from {{ source('bronze', 'ipeadata_indicadores') }}
)

select
    data::date                      as data_ref,
    date_trunc('month', data)::date as mes_ref,
    indicador,
    fonte                           as fonte_dado,
    valor::numeric(12,4)            as valor
from fonte
where valor is not null
  and data >= '2015-01-01'
order by data_ref, indicador

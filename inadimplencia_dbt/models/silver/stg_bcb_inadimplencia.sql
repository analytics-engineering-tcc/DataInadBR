with fonte as (
    select * from {{ source('bronze', 'bcb_inadimplencia') }}
)

select
    data::date                      as data_ref,
    date_trunc('month', data)::date as mes_ref,
    serie,
    descricao,
    valor::numeric(12,4)            as valor
from fonte
where valor is not null
  and data >= '2015-01-01'
order by data_ref, serie

# DataInadBR

Engenharia de Dados aplicada à Análise e Monitoramento da Inadimplência no Brasil: dos Dados Abertos ao Dashboard.

## Tecnologias
- Python
- PostgreSQL
- Apache Airflow
- dbt
- Power BI
- Docker

## Estrutura do projeto
- `data/bronze` — dados brutos das APIs
- `data/silver` — dados tratados pelo dbt
- `data/gold` — tabelas agregadas para o dashboard
- `dags/` — pipelines do Airflow
- `notebooks/` — análise exploratória
- `dashboard/` — arquivos Power BI
# DataInadBR

**Engenharia de Dados aplicada à Análise e Monitoramento da Inadimplência no Brasil: dos Dados Abertos ao Dashboard**

Trabalho de Conclusão de Curso (TCC) do Bacharelado em Sistemas de Informação — IFBA Campus Vitória da Conquista.

**Autora:** Caroline Feitosa dos Santos  
**Orientador:** Prof. Dr. Luis Paulo da Silva Carvalho  
**Período:** 2026

---

## Sobre o Projeto

O DataInadBR é um pipeline completo de engenharia de dados que coleta, transforma e disponibiliza indicadores públicos relacionados à inadimplência do crédito ao consumidor no Brasil. O projeto segue a **arquitetura Medallion** (Bronze → Silver → Gold) e utiliza ferramentas modernas de engenharia de dados para transformar dados brutos de APIs públicas em um dashboard interativo.

### Fontes de Dados

| Fonte | Séries / Indicadores |
|-------|---------------------|
| **BCB SGS API** | Taxa Selic, inadimplência PF/PJ, concessões de crédito, spread bancário, juros cartão de crédito, comprometimento de renda, provisão para créditos de liquidação duvidosa, carteira inadimplente |
| **IBGE** | Taxa de desemprego (PNAD Contínua), IPCA (inflação) |
| **IPEAdata** | PIB mensal, rendimento real habitual do trabalho |

### Arquitetura

```
APIs Públicas (BCB, IBGE, IPEAdata)
        │
        ▼
   ┌─────────┐
   │  Bronze  │  Dados brutos em CSV + PostgreSQL
   └────┬────┘
        │  dbt (views)
        ▼
   ┌─────────┐
   │  Silver  │  Dados limpos, tipados e deduplicados
   └────┬────┘
        │  dbt (tables)
        ▼
   ┌─────────┐
   │   Gold   │  Fato + dimensão para análise
   └────┬────┘
        │  Exportação JSON
        ▼
   ┌───────────┐
   │ Dashboard  │  HTML/JS com Chart.js
   └───────────┘
```

**Orquestração:** Apache Airflow executa duas DAGs programadas mensalmente:
1. `coleta_bronze` — 4 tasks paralelas de coleta (BCB principal, BCB complementar, IBGE, IPEAdata)
2. `transformacao_dbt` — dbt run → dbt test → exportação de JSONs para o dashboard

---

## Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| Linguagem | Python 3.13+ |
| Banco de Dados | PostgreSQL 15 |
| Orquestração | Apache Airflow 3.x |
| Transformação | dbt Core (dbt-postgres) |
| Dashboard | HTML, JavaScript, Chart.js 4.4.4 |
| Infraestrutura | Docker (PostgreSQL), UTM/QEMU (VM Ubuntu) |
| Versionamento | Git + GitHub |

---

## Estrutura do Projeto

```
DataInadBR/
├── dags/                          # DAGs do Airflow
│   ├── dag_coleta_bronze.py       # Coleta de dados das APIs públicas
│   └── dag_transformacao_dbt.py   # Transformação dbt + exportação JSON
├── scripts/                       # Scripts de coleta
│   ├── 01_coleta_bcb.py           # BCB — séries principais (inadimplência PF/PJ)
│   ├── 02_coleta_bcb_complementar.py  # BCB — séries complementares (Selic, spread, etc.)
│   ├── 03_coleta_ibge.py          # IBGE — desemprego e IPCA
│   ├── 04_coleta_ipeadata.py      # IPEAdata — PIB e rendimento real
│   └── exportar_gold_json.py      # Exporta tabelas Gold para JSON
├── inadimplencia_dbt/             # Projeto dbt
│   ├── dbt_project.yml
│   ├── models/
│   │   ├── silver/                # Views — staging limpo
│   │   │   ├── stg_bcb_inadimplencia.sql
│   │   │   ├── stg_ibge_indicadores.sql
│   │   │   ├── stg_ipeadata_indicadores.sql
│   │   │   ├── sources.yml
│   │   │   └── schema.yml         # Testes not_null
│   │   └── gold/                  # Tables — fato e dimensão
│   │       ├── fct_inadimplencia_mensal.sql
│   │       └── dim_tempo.sql
│   └── macros/
│       └── custom_schema.sql      # Roteamento de schemas
├── dashboard/                     # Dashboard interativo
│   ├── index.html                 # Página principal com gráficos
│   ├── logo_ifba.png
│   └── data/                      # JSONs exportados pelo pipeline
│       ├── fct_inadimplencia_mensal.json
│       ├── dim_tempo.json
│       └── kpis_ultimo_mes.json
├── data/                          # Dados brutos (CSVs da camada Bronze)
│   └── bronze/
├── docker-compose.yml             # PostgreSQL containerizado
├── docs/                          # Documentação adicional
├── notebooks/                     # Notebooks exploratórios
├── .env                           # Variáveis de ambiente (não versionado)
└── README.md
```

---

## Pré-requisitos

- Python 3.13+
- PostgreSQL 15
- Docker e Docker Compose (para PostgreSQL no Mac)
- Git

---

## Instalação e Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/analytics-engineering-tcc/DataInadBR.git
cd DataInadBR
```

### 2. Criar e ativar o ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install --break-system-packages apache-airflow dbt-postgres pandas requests sqlalchemy python-dotenv
```

### 4. Configurar o banco de dados

**Com Docker (recomendado):**
```bash
docker compose up -d
```

**Ou PostgreSQL nativo:** crie o banco `inadimplencia` com usuário `tcc`.

### 5. Configurar variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto:

```env
DB_USER=tcc
DB_PASSWORD=tcc123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=inadimplencia
```

### 6. Criar os schemas no banco

```sql
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
```

### 7. Criar pasta de dados

```bash
mkdir -p data/bronze
```

---

## Execução

### Via Airflow (recomendado)

```bash
# Definir variáveis de ambiente
export DB_USER=tcc DB_PASSWORD=tcc123 DB_HOST=localhost DB_PORT=5432 DB_NAME=inadimplencia

# Iniciar o Airflow
airflow standalone
```

Acesse `http://localhost:8080` (Airflow). Para obter a senha de login:

```bash
cat ~/airflow/simple_auth_manager_passwords.json.generated
```

O usuário padrão é `admin`. Despause as DAGs e acione:
1. **coleta_bronze** — coleta os dados das APIs
2. **transformacao_dbt** — transforma e exporta para o dashboard

### Via linha de comando (manual)

```bash
# Coleta
python scripts/01_coleta_bcb.py
python scripts/02_coleta_bcb_complementar.py
python scripts/03_coleta_ibge.py
python scripts/04_coleta_ipeadata.py

# Transformação dbt
cd inadimplencia_dbt
dbt run
dbt test
cd ..

# Exportação JSON
python scripts/exportar_gold_json.py
```

### Visualizar o dashboard

```bash
cd dashboard
python3 -m http.server 8081
```

Acesse `http://localhost:8081` no navegador.

> **Nota:** O Airflow usa a porta 8080, por isso o dashboard é servido na porta 8081. Se o Airflow não estiver rodando, pode usar a porta 8080.

---

## Modelos dbt

### Silver (Views — Staging)

| Modelo | Descrição |
|--------|-----------|
| `stg_bcb_inadimplencia` | Dados BCB limpos e deduplicados |
| `stg_ibge_indicadores` | Indicadores IBGE padronizados |
| `stg_ipeadata_indicadores` | Indicadores IPEAdata padronizados |

### Gold (Tables — Analítico)

| Modelo | Descrição |
|--------|-----------|
| `fct_inadimplencia_mensal` | Tabela fato com todos os indicadores mensais consolidados |
| `dim_tempo` | Dimensão temporal (ano, mês, trimestre) |

### Testes de qualidade

7 testes `not_null` configurados em `schema.yml` validando campos críticos (`data_ref`, `valor`, `serie`).

---

## Dashboard

O dashboard interativo exibe:

- **KPIs** do último mês disponível (inadimplência PF/PJ, Selic, desemprego, IPCA, PIB)
- **6 gráficos de linha** com evolução temporal dos indicadores
- **4 gráficos de dispersão** mostrando correlações entre variáveis
- **Filtros de período** (mês/ano inicial e final)

Construído com HTML puro, JavaScript e Chart.js 4.4.4, sem dependências de servidor — consome JSONs estáticos exportados pelo pipeline.

---

## Execução na VM (Máquina Virtual)

O projeto inclui uma máquina virtual Ubuntu preparada para execução completa do pipeline, sem necessidade de instalar nada além do virtualizador.

### Especificações da VM

| Item | Detalhe |
|------|---------|
| Sistema | Ubuntu 26.04 LTS (aarch64) |
| Virtualização | UTM (macOS) / QEMU (Linux/Windows) |
| Hostname | `datainadbr` |
| Usuário | `tcc` / Senha: `tcc123` |
| Projeto | `~/DataInadBR` |
| PostgreSQL | 15 (nativo, já configurado) |
| Python | 3.14 |
| Airflow | 3.4.0 |
| dbt Core | dbt-postgres instalado |

### Passo a passo para rodar na VM

#### 1. Abrir a VM

- **macOS:** Abra o UTM e importe o arquivo `DataInadBR.utm`. Inicie a VM.
- **Linux/Windows:** Use o QEMU para importar a imagem.

#### 2. Acessar via SSH (do computador host)

```bash
ssh tcc@192.168.64.2
```

Senha: `tcc123`

> **Nota:** O IP pode variar. Caso não conecte, verifique o IP da VM com `ip addr` diretamente no terminal da VM.

#### 3. Ativar o ambiente e variáveis

```bash
cd ~/DataInadBR
source venv/bin/activate
export DB_USER=tcc DB_PASSWORD=tcc123 DB_HOST=localhost DB_PORT=5432 DB_NAME=inadimplencia
```

#### 4. Verificar que o PostgreSQL está rodando

```bash
sudo systemctl status postgresql
```

Se não estiver ativo:

```bash
sudo systemctl start postgresql
```

#### 5. Criar pasta de dados (se necessário)

```bash
mkdir -p data/bronze
```

#### 6. Iniciar o Airflow

```bash
airflow standalone
```

#### 7. Obter a senha do Airflow

Em outro terminal SSH (`ssh tcc@192.168.64.2`):

```bash
cat ~/airflow/simple_auth_manager_passwords.json.generated
```

#### 8. Acessar o Airflow no navegador (do host)

Acesse `http://192.168.64.2:8080` e faça login com usuário `admin` e a senha obtida no passo anterior.

#### 9. Executar o pipeline

1. Despause a DAG **coleta_bronze** (toggle à esquerda do nome)
2. Clique em **▶ Acionar** para disparar a coleta
3. Aguarde todas as 4 tarefas ficarem verdes (≈ 3-5 minutos)
4. Despause a DAG **transformacao_dbt**
5. Clique em **▶ Acionar** para disparar a transformação
6. Aguarde as 3 tarefas ficarem verdes (dbt run → dbt test → exportar JSON)

#### 10. Visualizar o dashboard

Em outro terminal SSH:

```bash
cd ~/DataInadBR/dashboard
python3 -m http.server 8081
```

Acesse `http://192.168.64.2:8081` no navegador do host.

> **Resumo de portas na VM:**
> - `8080` — Airflow (interface web)
> - `8081` — Dashboard (visualização dos dados)

---

## Licença

Projeto acadêmico — IFBA Campus Vitória da Conquista, 2026.

---

## Repositório

[github.com/analytics-engineering-tcc/DataInadBR](https://github.com/analytics-engineering-tcc/DataInadBR)
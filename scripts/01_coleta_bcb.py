import requests
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# carrega as credenciais do .env
load_dotenv()

DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")

# conexão com o banco
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

def coleta_bcb(serie, descricao, inicio, fim):
    print(f"Coletando série {serie} — {descricao}...")
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
    params = {
        "formato": "json",
        "dataInicial": inicio,
        "dataFinal": fim
    }
    r = requests.get(url, params=params)
    df = pd.DataFrame(r.json())
    df["data"]      = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"]     = pd.to_numeric(df["valor"], errors="coerce")
    df["serie"]     = str(serie)
    df["descricao"] = descricao
    return df

# séries que vamos coletar
series = [
    (21082, "Inadimplência PF"),
    (21112, "Inadimplência PJ"),
    (13522, "Endividamento das famílias"),
]

# coleta e salva no banco
for serie, descricao in series:
    df = coleta_bcb(serie, descricao, "01/01/2015", "31/12/2024")

    # salva CSV na camada bronze
    df.to_csv(f"data/bronze/bcb_{serie}.csv", index=False)
    print(f"  CSV salvo em data/bronze/bcb_{serie}.csv")

    # salva no PostgreSQL
    df.to_sql(       schema="bronze",
        if_exists="append",
        index=False
    )
    print(f"  Dados carregados no banco — {len(df)} registros")

print("\nColeta concluída!")
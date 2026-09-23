import requests
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def coleta_bcb(serie, descricao, inicio, fim):
    print(f"Coletando série {serie} — {descricao}...")
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
    params = {"formato": "json", "dataInicial": inicio, "dataFinal": fim}
    r = requests.get(url, params=params)
    df = pd.DataFrame(r.json())
    df["data"]      = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"]     = pd.to_numeric(df["valor"], errors="coerce")
    df["serie"]     = str(serie)
    df["descricao"] = descricao
    return df

series = [
    (11,    "Taxa Selic"),
    (13685, "Provisao para creditos de liquidacao duvidosa"),
    (15882, "Carteira inadimplente total"),
]

for serie, descricao in series:
    try:
        df = coleta_bcb(serie, descricao, "01/01/2015", "31/12/2024")
        df.to_csv(f"data/bronze/bcb_{serie}.csv", index=False)
        print(f"  CSV salvo — {len(df)} registros")
        df.to_sql(
            "bcb_inadimplencia",
            engine,
            schema="bronze",
            if_exists="append",
            index=False
        )
        print(f"  Banco atualizado!")
    except Exception as e:
        print(f"  ERRO na série {serie}: {e}")

print("\nColeta complementar concluída!")
import requests
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# =============================================
# IPEAdata — API OData
# Docs: http://www.ipeadata.gov.br/api/
# =============================================

def coleta_ipeadata(serie_codigo, descricao):
    """Coleta dados da API do IPEAdata."""
    print(f"Coletando IPEAdata {serie_codigo} — {descricao}...")
    url = f"http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{serie_codigo}')"
    r = requests.get(url)
    dados = r.json()["value"]

    registros = []
    for item in dados:
        registros.append({
            "data":  item["VALDATA"],
            "valor": item["VALVALOR"],
        })

    df = pd.DataFrame(registros)
    df["data"]  = pd.to_datetime(df["data"], utc=True)
    df["data"]  = df["data"].dt.tz_localize(None)
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    # filtra período de interesse (2015–2024)
    df = df[(df["data"] >= "2015-01-01") & (df["data"] <= "2024-12-31")]

    df["fonte"]     = "IPEAdata"
    df["indicador"] = descricao
    df = df[["data", "valor", "fonte", "indicador"]]
    return df


# =============================================
# Indicadores IPEAdata
# =============================================

indicadores = [
    # (código da série, descrição)
    ("BM12_PIB12",     "PIB mensal"),
    ("PNADC12_RRTH12", "Rendimento medio real habitual"),
]

for serie_codigo, descricao in indicadores:
    try:
        df = coleta_ipeadata(serie_codigo, descricao)

        nome_csv = descricao.lower().replace(" ", "_")
        caminho = f"data/bronze/ipeadata_{nome_csv}.csv"
        df.to_csv(caminho, index=False)
        print(f"  CSV salvo: {caminho} — {len(df)} registros")

        df.to_sql(
            "ipeadata_indicadores",
            engine,
            schema="bronze",
            if_exists="append",
            index=False
        )
        print(f"  Banco atualizado!")
    except Exception as e:
        print(f"  ERRO {descricao}: {e}")

print("\nColeta IPEAdata concluída!")
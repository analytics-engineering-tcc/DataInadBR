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
# IBGE — API de Agregados
# Docs: https://servicodados.ibge.gov.br/api/docs/agregados
# =============================================

def coleta_ibge(agregado, variavel, descricao, periodicidade="mensal"):
    """
    Coleta dados da API de Agregados do IBGE.
    periodicidade: 'mensal' ou 'trimestral_movel'
    """
    print(f"Coletando IBGE agregado {agregado} — {descricao}...")
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{agregado}"
        f"/periodos/-120/variaveis/{variavel}"
    )
    params = {"localidades": "N1[all]"}
    r = requests.get(url, params=params)
    dados = r.json()

    # a resposta do IBGE é um JSON aninhado
    serie = dados[0]["resultados"][0]["series"][0]["serie"]

    registros = []
    for periodo, valor in serie.items():
        if valor and valor != "..." and valor != "-":
            registros.append({
                "periodo_original": periodo,
                "valor": float(valor),
            })

    df = pd.DataFrame(registros)

    if periodicidade == "trimestral_movel":
        # formato IBGE trimestre móvel: "202308" = trimestre iniciando em agosto/2023
        # usamos o mês inicial como referência
        df["data"] = df["periodo_original"].apply(
            lambda p: pd.Timestamp(f"{p[:4]}-{p[4:6]}-01")
        )
    else:
        # formato mensal: "202301" = janeiro de 2023
        df["data"] = pd.to_datetime(df["periodo_original"], format="%Y%m")

    # filtra período de interesse (2015–2024)
    df = df[(df["data"] >= "2015-01-01") & (df["data"] <= "2024-12-31")]

    df["fonte"]     = "IBGE"
    df["indicador"] = descricao
    df = df[["data", "valor", "fonte", "indicador"]]
    return df


# =============================================
# Indicadores IBGE
# =============================================

indicadores = [
    # (agregado, variável, descrição, periodicidade)
    (6381, 4099, "Taxa de desocupacao", "trimestral_movel"),
    (7060, 63,   "IPCA variacao mensal", "mensal"),
]

for agregado, variavel, descricao, periodicidade in indicadores:
    try:
        df = coleta_ibge(agregado, variavel, descricao, periodicidade)

        nome_csv = descricao.lower().replace(" ", "_")
        caminho = f"data/bronze/ibge_{nome_csv}.csv"
        df.to_csv(caminho, index=False)
        print(f"  CSV salvo: {caminho} — {len(df)} registros")

        df.to_sql(
            "ibge_indicadores",
            engine,
            schema="bronze",
            if_exists="append",
            index=False
        )
        print(f"  Banco atualizado!")
    except Exception as e:
        print(f"  ERRO {descricao}: {e}")

print("\nColeta IBGE concluída!")
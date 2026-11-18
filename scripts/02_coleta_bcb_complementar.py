import requests
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from datetime import date, datetime, timedelta

load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def gerar_janelas(inicio_str, fim_str, max_anos=9):
    """Divide o intervalo em janelas de no máximo max_anos para respeitar o limite da API BCB."""
    inicio = datetime.strptime(inicio_str, "%d/%m/%Y")
    fim = datetime.strptime(fim_str, "%d/%m/%Y")
    janelas = []
    cursor = inicio
    while cursor < fim:
        limite = cursor.replace(year=cursor.year + max_anos)
        if limite > fim:
            limite = fim
        janelas.append((cursor.strftime("%d/%m/%Y"), limite.strftime("%d/%m/%Y")))
        cursor = limite + timedelta(days=1)
    return janelas

def coleta_bcb(serie, descricao, inicio, fim):
    print(f"Coletando série {serie} — {descricao}...")
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
    janelas = gerar_janelas(inicio, fim)
    dados = []
    for ini, f in janelas:
        print(f"  Janela: {ini} a {f}")
        params = {"formato": "json", "dataInicial": ini, "dataFinal": f}
        r = requests.get(url, params=params)
        resposta = r.json()
        if isinstance(resposta, list):
            dados.extend(resposta)
        else:
            print(f"  Aviso: resposta inesperada para janela {ini}-{f}: {resposta}")
    df = pd.DataFrame(dados)
    df["data"]      = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"]     = pd.to_numeric(df["valor"], errors="coerce")
    df["serie"]     = str(serie)
    df["descricao"] = descricao
    return df

series = [
    (11,    "Taxa Selic"),
    (13685, "Provisao para creditos de liquidacao duvidosa"),
    (15882, "Carteira inadimplente total"),
    (20614, "Comprometimento de renda PF"),
    (7384,  "Juros cartao de credito"),
    (20783, "Spread bancario geral"),
    (20539, "Concessoes de credito PF"),
    (20541, "Concessoes de credito PJ"),
]

for serie, descricao in series:
    try:
        df = coleta_bcb(serie, descricao, "01/01/2015", date.today().strftime("%d/%m/%Y"))
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
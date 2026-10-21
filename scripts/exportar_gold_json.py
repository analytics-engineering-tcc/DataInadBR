"""
Exporta as tabelas Gold do PostgreSQL para arquivos JSON
que o dashboard HTML/JS vai consumir.
"""

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# Conexão
ENGINE = create_engine("postgresql://tcc:tcc123@localhost:5432/inadimplencia")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "data"


def serializar_datas(obj):
    """Converte date/datetime para string ISO nos JSONs."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Tipo {type(obj)} não serializável")


def exportar():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Tabela fato — inadimplência mensal com indicadores macro
    fct = pd.read_sql("SELECT * FROM gold.fct_inadimplencia_mensal ORDER BY mes_ref, serie", ENGINE)
    fct.to_json(OUTPUT_DIR / "fct_inadimplencia_mensal.json", orient="records", date_format="iso", force_ascii=False)
    print(f"✅ fct_inadimplencia_mensal: {len(fct)} registros")

    # 2. Dimensão tempo
    dim = pd.read_sql("SELECT * FROM gold.dim_tempo ORDER BY data_ref", ENGINE)
    dim.to_json(OUTPUT_DIR / "dim_tempo.json", orient="records", date_format="iso", force_ascii=False)
    print(f"✅ dim_tempo: {len(dim)} registros")

    # 3. Resumo para KPIs — últimos valores disponíveis de cada indicador
    # 3. Resumo para KPIs — último valor disponível de cada série
    kpis = pd.read_sql("""
        SELECT DISTINCT ON (serie)
            serie,
            descricao,
            valor_indicador,
            taxa_desocupacao,
            ipca_variacao,
            pib_mensal,
            rendimento_real,
            mes_ref
        FROM gold.fct_inadimplencia_mensal
        WHERE valor_indicador IS NOT NULL
        ORDER BY serie, mes_ref DESC
    """, ENGINE)
    kpis.to_json(OUTPUT_DIR / "kpis_ultimo_mes.json", orient="records", date_format="iso", force_ascii=False)
    print(f"✅ kpis_ultimo_mes: {len(kpis)} registros")


if __name__ == "__main__":
    exportar()
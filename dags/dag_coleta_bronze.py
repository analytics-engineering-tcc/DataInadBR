"""
DAG de Coleta — Camada Bronze
=============================
Orquestra os 4 scripts de coleta de dados (BCB, IBGE, IPEAdata),
ingerindo os dados brutos na camada Bronze do PostgreSQL.

Schedule: dia 5 de cada mês (dados oficiais costumam ser publicados
nos primeiros dias úteis do mês seguinte ao período de referência).
"""

from datetime import datetime, timedelta
from pathlib import Path
from airflow.sdk import DAG, task

import subprocess
import os

# ----- Configurações -----

# Caminho base do projeto — ajuste se necessário
PROJETO_DIR = os.environ.get(
    "DATAINADBR_PROJECT_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
SCRIPTS_DIR = os.path.join(PROJETO_DIR, "scripts")

# Argumentos padrão para todas as tasks
default_args = {
    "owner": "carol",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


# ----- Funções de execução -----

def rodar_script(nome_script: str):
    """Executa um script Python da pasta scripts/ usando o Python do venv."""
    caminho = Path(__file__).resolve().parent.parent / "scripts" / nome_script
    python_venv = Path(__file__).resolve().parent.parent / "venv" / "bin" / "python"
    resultado = subprocess.run(
        [str(python_venv), str(caminho)],
        capture_output=True,
        text=True,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"Falha ao executar {nome_script}: {resultado.stderr}"
        )
    print(resultado.stdout)


# ----- DAG -----

with DAG(
    dag_id="coleta_bronze",
    description="Coleta mensal de dados brutos (BCB, IBGE, IPEAdata) para a camada Bronze",
    schedule="0 6 5 * *",  # todo dia 5 do mês, às 06:00 UTC (03:00 BRT)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["bronze", "coleta", "datainadbr"],
    default_args=default_args,
) as dag:

    # ---- Tasks ----

    @task(task_id="coleta_bcb_principal")
    def coleta_bcb_principal():
        """Coleta as 3 séries BCB principais: inadimplência PF/PJ e endividamento."""
        rodar_script("01_coleta_bcb.py")

    @task(task_id="coleta_bcb_complementar")
    def coleta_bcb_complementar():
        """Coleta as 8 séries BCB complementares: Selic, spread, juros, concessões etc."""
        rodar_script("02_coleta_bcb_complementar.py")

    @task(task_id="coleta_ibge")
    def coleta_ibge():
        """Coleta indicadores IBGE: taxa de desocupação (PNAD) e IPCA."""
        rodar_script("03_coleta_ibge.py")

    @task(task_id="coleta_ipeadata")
    def coleta_ipeadata():
        """Coleta indicadores IPEAdata: PIB mensal e rendimento real."""
        rodar_script("04_coleta_ipeadata.py")

    # ---- Dependências ----
    # Todas as fontes rodam em paralelo — não há dependência entre elas.

    coleta_bcb_principal()
    coleta_bcb_complementar()
    coleta_ibge()
    coleta_ipeadata()
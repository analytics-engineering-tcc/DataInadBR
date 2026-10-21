from airflow.sdk import dag, task
from pendulum import datetime
import subprocess
from pathlib import Path

# Caminhos do projeto
PROJECT_DIR = Path.home() / "Desktop" / "DataInadBR"
DBT_DIR = PROJECT_DIR / "inadimplencia_dbt"
DBT_BIN = PROJECT_DIR / "venv" / "bin" / "dbt"


@dag(
    dag_id="transformacao_dbt",
    description="Transforma dados Bronze → Silver → Gold usando dbt",
    schedule="0 7 5 * *",  # dia 5 de cada mês às 07:00 UTC (1h após coleta)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "silver", "gold", "transformacao"],
)
def transformacao_dbt():

    @task()
    def dbt_run():
        """Executa todos os models dbt (Silver views + Gold tables)"""
        result = subprocess.run(
            [str(DBT_BIN), "run"],
            cwd=str(DBT_DIR),
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise Exception(f"dbt run falhou:\n{result.stderr}")
        return "dbt run OK"

    @task()
    def dbt_test():
        """Executa os testes de qualidade dos dados"""
        result = subprocess.run(
            [str(DBT_BIN), "test"],
            cwd=str(DBT_DIR),
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise Exception(f"dbt test falhou:\n{result.stderr}")
        return "dbt test OK"

    # Sequência: primeiro transforma, depois testa
    dbt_run() >> dbt_test()


transformacao_dbt()

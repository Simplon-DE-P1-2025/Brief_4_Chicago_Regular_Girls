from airflow.decorators import dag, task
from airflow.providers.postgres.operators.postgres import PostgresOperator # L'import clé
from datetime import datetime
from include.scripts.ingestion import ingest_chicago_data

@dag(
    schedule_interval='@daily',
    start_date=datetime(2026, 3, 10),
    template_searchpath=['/usr/local/airflow/include/sql'], # Astro CLI cherche ici
    catchup=False,
)
def chicago_crimes_pipeline():

    # TASK 1 : Initialisation de la table (Simple et efficace)
    setup_db = PostgresOperator(
        task_id='init_postgres_table',
        postgres_conn_id='postgres_default',
        sql='init_db.sql', # Nom du fichier dans include/sql/
    )

    # TASK 2 : Ingestion (Votre logique Python)
    @task
    def run_ingestion():
        return ingest_chicago_data(postgres_conn_id='postgres_default')

    # ORCHESTRATION : On définit l'ordre (Setup d'abord, Ingestion ensuite)
    setup_db >> run_ingestion()

chicago_crimes_dag = chicago_crimes_pipeline()
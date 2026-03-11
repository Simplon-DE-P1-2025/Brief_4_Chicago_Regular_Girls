from airflow.decorators import dag, task
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
from include.etl.ingestion import ingest_chicago_data
import logging

@dag(
    schedule_interval='@daily',
    start_date=datetime(2026, 3, 10),
    template_searchpath=['/usr/local/airflow/include/sql'],
    catchup=False,
)
def chicago_crimes_pipeline():

    setup_db = PostgresOperator(
        task_id='init_postgres_table',
        postgres_conn_id='postgres_default',
        sql='init_db.sql',
    )

    @task
    def run_ingestion():
        return ingest_chicago_data(postgres_conn_id='postgres_default')

    @task
    def soda_check_raw():
        from soda.scan import Scan

        conn = PostgresHook(postgres_conn_id='postgres_default').get_connection('postgres_default')

        scan = Scan()
        scan.set_scan_definition_name("chicago_raw_check")
        scan.set_data_source_name("chicago_pg")

        scan.add_configuration_yaml_str(f"""
data_source chicago_pg:
  type: postgres
  host: {conn.host}
  port: {conn.port or 5432}
  database: {conn.schema}
  username: {conn.login}
  password: {conn.password}
  schema: raw
""")

        scan.add_sodacl_yaml_str(open('/usr/local/airflow/include/soda/checks_raw.yml').read())

        scan.execute()
        logging.info(scan.get_logs_text())

        if scan.has_check_fails():
            failed = [c.name for c in scan.get_checks() if c.outcome and c.outcome.name == "fail"]
            raise ValueError(f" SODA Check #1 ÉCHOUÉ — pipeline arrêté : {failed}")

        logging.info(" SODA Check #1 OK")

    transform_sql = PostgresOperator(
        task_id='transform_sql',
        postgres_conn_id='postgres_default',
        sql='transform.sql',
    )

    @task
    def soda_check_clean():
        from soda.scan import Scan

        conn = PostgresHook(postgres_conn_id='postgres_default').get_connection('postgres_default')

        scan = Scan()
        scan.set_scan_definition_name("chicago_clean_check")
        scan.set_data_source_name("chicago_pg")

        scan.add_configuration_yaml_str(f"""
data_source chicago_pg:
  type: postgres
  host: {conn.host}
  port: {conn.port or 5432}
  database: {conn.schema}
  username: {conn.login}
  password: {conn.password}
  schema: silver
""")

        scan.add_sodacl_yaml_str(open('/usr/local/airflow/include/soda/checks_clean.yml').read())

        scan.execute()
        logging.info(scan.get_logs_text())

        if scan.has_check_fails():
            failed = [c.name for c in scan.get_checks() if c.outcome and c.outcome.name == "fail"]
            raise ValueError(f" SODA Check #2 ÉCHOUÉ : {failed}")

        logging.info(" SODA Check #2 OK — données prêtes !")

    setup_db >> run_ingestion() >> soda_check_raw() >> transform_sql >> soda_check_clean()


chicago_crimes_dag = chicago_crimes_pipeline()

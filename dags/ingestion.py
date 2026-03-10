import requests
import pandas as pd
import time
from airflow.providers.postgres.hooks.postgres import PostgresHook

def ingest_chicago_data(postgres_conn_id, limit=50000):
    """
    Logique pure d'ingestion de l'API Chicago vers Postgres
    """
    base_url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
    pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    
    offset = 0
    has_more = True
    total_rows = 0

    while has_more:
        params = {
            "$where": "year >= 2020",
            "$limit": limit,
            "$offset": offset,
            "$order": ":id"
        }
        
        print(f"Extraction des lignes {offset} à {offset + limit}...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            has_more = False
            break

        df = pd.DataFrame(data)
        
        # Insertion dans Render
        df.to_sql(
            'chicago_crimes', # Le nom de la table uniquement
            con=pg_hook.get_sqlalchemy_engine(),
            schema='raw',     # AJOUT : On précise le schéma ici
            if_exists='append',
            index=False
        )
        
        total_rows += len(data)
        offset += limit
        time.sleep(1) 

    return total_rows
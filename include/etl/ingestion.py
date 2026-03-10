import requests
import pandas as pd
import time
from airflow.providers.postgres.hooks.postgres import PostgresHook

def ingest_chicago_data(postgres_conn_id, limit=50000):
    """
    Ingestion complète de l'API Chicago Crimes vers le schéma raw de Postgres.
    Gère la pagination, le typage et l'ID technique (SERIAL).
    """
    base_url = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
    pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
    
    offset = 0
    has_more = True
    total_rows = 0

    while has_more:
        # 1. Requête à l'API avec SoQL (Période 2020+)
        params = {
            "$where": "year >= 2020",
            "$limit": limit,
            "$offset": offset,
            "$order": ":id" # Indispensable pour une pagination stable
        }
        
        print(f"Extraction Chicago API : Lignes {offset} à {offset + limit}...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print("Fin de l'ingestion : plus de nouvelles données.")
            has_more = False
            break

        # 2. Chargement dans un DataFrame Pandas
        df = pd.DataFrame(data)

        # --- PHASE DE TRANSFORMATION & MAPPING ---
        
        # A. Gestion de l'ID (Renommer l'ID API en chicago_id)
        if 'id' in df.columns:
            df = df.rename(columns={'id': 'chicago_id'})

        # B. Conversion des Dates (Format TIMESTAMP)
        date_cols = ['date', 'updated_on']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # C. Conversion des Numeriques (Format INTEGER / DOUBLE PRECISION)
        # On inclut chicago_id qui est devenu une Natural Key
        int_cols = ['chicago_id', 'ward', 'community_area', 'year']
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        float_cols = ['latitude', 'longitude']
        for col in float_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # D. Conversion des Booleans (Postgres n'aime pas les strings 'true'/'false')
        bool_cols = ['arrest', 'domestic']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].map({'true': True, 'false': False, True: True, False: False})

        # E. Filtrage strict (On ne garde que ce qui est dans le init_db.sql)
        # ATTENTION : On n'envoie PAS de colonne 'id' car elle est SERIAL en base
        allowed_columns = [
            'chicago_id', 'case_number', 'date', 'block', 'iucr', 'primary_type', 
            'description', 'location_description', 'arrest', 'domestic', 
            'beat', 'district', 'ward', 'community_area', 'fbi_code', 
            'year', 'updated_on', 'latitude', 'longitude'
        ]
        df = df[[col for col in allowed_columns if col in df.columns]]

        # 3. Insertion dans Render (Optimisée)
        engine = pg_hook.get_sqlalchemy_engine()
        with engine.begin() as conn:
            df.to_sql(
                name='raw_chicago_crimes', 
                con=conn,
                schema='raw', 
                if_exists='append', 
                index=False,
                method='multi', # Envoie les lignes par paquets (très rapide)
                chunksize=1000  # Evite de saturer la connexion
            )
        
        total_rows += len(data)
        offset += limit
        print(f"Succès : {len(data)} lignes insérées. (Total : {total_rows})")
        
        # Respecter les limites de l'API Chicago
        time.sleep(1) 

    return total_rows
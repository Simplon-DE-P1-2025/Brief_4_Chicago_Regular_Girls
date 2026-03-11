# 🚔 Chicago Crimes — Pipeline de données

Pipeline ETL automatisé pour l'ingestion, la transformation et la validation des données de criminalité de la ville de Chicago. Orchestré avec **Apache Airflow**, stocké dans **PostgreSQL**, et validé avec **SODA**.

---

## 📐 Architecture

```
Chicago Open Data API
        │
        ▼
┌───────────────────┐
│   raw schema      │  ← Données brutes (raw_chicago_crimes)
│   PostgreSQL      │
└───────────────────┘
        │
        ▼  transform.sql
┌───────────────────┐
│  silver schema    │  ← Données nettoyées (chicago_crimes_clean)
│   PostgreSQL      │
└───────────────────┘
```

## 🔄 DAG Airflow — `chicago_crimes_pipeline`

Le pipeline s'exécute **quotidiennement** (`@daily`) et enchaîne 5 étapes :

```
init_postgres_table
        │
        ▼
  run_ingestion          ← Appel API paginé + insertion en raw
        │
        ▼
  soda_check_raw         ← Validation qualité données brutes
        │
        ▼
  transform_sql          ← Nettoyage + filtrage géographique
        │
        ▼
  soda_check_clean       ← Validation qualité données nettoyées
```

---

## 📁 Structure du projet

```
.
├── dags/
│   └── chicago_crimes_dag.py        # Définition du DAG Airflow
│
├── include/
│   ├── etl/
│   │   ├── __init__.py
│   │   ├── ingestion.py             # Ingestion API → raw
│   │   └── transformation.py        # (réservé aux transformations Python)
│   │
│   ├── sql/
│   │   ├── init_db.sql              # Création des schémas et tables
│   │   └── transform.sql            # Transformation raw → silver
│   │
│   └── soda/
│       ├── checks_raw.yml           # Checks qualité sur raw_chicago_crimes
│       └── checks_clean.yml         # Checks qualité sur chicago_crimes_clean
│
├── Dockerfile                       # Image Airflow personnalisée
└── uv.lock                          # Dépendances Python (uv)
```

---

## 🗄️ Modèle de données

### `raw.raw_chicago_crimes`
Données brutes issues de l'API, sans transformation métier.

| Colonne | Type | Description |
|---|---|---|
| `id` | SERIAL PK | ID technique PostgreSQL |
| `chicago_id` | INTEGER | ID original de l'API Chicago |
| `case_number` | VARCHAR(20) | Numéro de dossier |
| `date` | TIMESTAMP | Date du crime |
| `primary_type` | VARCHAR(100) | Catégorie principale |
| `description` | VARCHAR(255) | Description détaillée |
| `arrest` | BOOLEAN | Arrestation effectuée |
| `domestic` | BOOLEAN | Incident domestique |
| `latitude` / `longitude` | DOUBLE PRECISION | Coordonnées GPS |
| `year` | INTEGER | Année du crime |

### `silver.chicago_crimes_clean`
Données nettoyées, filtrées géographiquement, prêtes à l'analyse.

| Colonne | Type | Transformation appliquée |
|---|---|---|
| `id` | INTEGER PK | ID source conservé |
| `crime_date` | TIMESTAMP | Renommage de `date` |
| `primary_type` | VARCHAR(100) | `UPPER(TRIM(...))` |
| `description` | VARCHAR(255) | `INITCAP(TRIM(...))` |
| `location_description` | VARCHAR(255) | `INITCAP(TRIM(...))` |
| `loaded_at` | TIMESTAMP | Horodatage du chargement |

---

## ✅ Contrôles qualité SODA

### Check #1 — `raw_chicago_crimes`
| Règle | Critère |
|---|---|
| Table non vide | `row_count > 0` |
| Volume suffisant | `row_count > 1000` |
| Pas d'ID manquant | `missing_count(id) = 0` |
| IDs uniques | `duplicate_count(id) = 0` |
| Dates présentes | `missing_count(date) = 0` |
| Type de crime | `missing_count(primary_type) < 500` |

### Check #2 — `chicago_crimes_clean`
| Règle | Critère |
|---|---|
| Volume post-transform | `row_count between 1000 and 25000` |
| Intégrité des IDs | `missing` et `duplicate = 0` |
| Coordonnées présentes | `missing_count(latitude/longitude) = 0` |
| Bornes géographiques Chicago | `lat ∈ [41.6, 42.1]`, `lon ∈ [-87.95, -87.5]` |

> En cas d'échec d'un check, le pipeline est **interrompu immédiatement** et une exception est levée avec le détail des checks échoués.

---

## 🔌 Source de données

- **API** : [Chicago Data Portal — Crimes](https://data.cityofchicago.org/resource/ijzp-q8t2.json)
- **Filtre temporel** : années 2020 et suivantes (`year >= 2020`)
- **Pagination** : 50 000 lignes par requête avec `$offset` + délai de 1 seconde entre les appels
- **Volume attendu** : plusieurs centaines de milliers de lignes

---

## ⚙️ Configuration

### Prérequis
- Docker & Docker Compose
- Connexion Airflow `postgres_default` configurée (host, port, database, login, password)


## 🛠️ Stack technique

| Outil | Rôle |
|---|---|
| **Apache Airflow** | Orchestration du pipeline |
| **PostgreSQL** | Stockage des données (raw + silver) |
| **Pandas** | Manipulation des DataFrames lors de l'ingestion |
| **SODA** | Contrôle qualité des données |
| **Docker** | Conteneurisation de l'environnement |
| **uv** | Gestion des dépendances Python |

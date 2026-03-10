-- 1. Création des schémas (Couches de données)
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS silver;

-- 2. Création de la table 'raw' pour les données brutes

CREATE TABLE IF NOT EXISTS raw.raw_chicago_crimes (
    id SERIAL PRIMARY KEY,        -- Ton ID unique géré par Postgres
    chicago_id INTEGER,
    case_number VARCHAR(20),
    date TIMESTAMP,
    block VARCHAR(255),
    iucr VARCHAR(10),
    primary_type VARCHAR(100),
    description VARCHAR(255),
    location_description VARCHAR(255),
    arrest BOOLEAN,
    domestic BOOLEAN,
    beat VARCHAR(10),
    district VARCHAR(10),
    ward INTEGER,
    community_area INTEGER,
    fbi_code VARCHAR(10),
    year INTEGER,
    updated_on TIMESTAMP,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
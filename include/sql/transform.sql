TRUNCATE TABLE silver.chicago_crimes_clean;

INSERT INTO silver.chicago_crimes_clean (
    id, case_number, crime_date, primary_type, description,
    location_description, arrest, domestic, district,
    community_area, latitude, longitude, year, loaded_at
)
SELECT
    id,
    case_number,
    date                          AS crime_date,
    UPPER(TRIM(primary_type))     AS primary_type,
    INITCAP(TRIM(description))    AS description,
    INITCAP(TRIM(location_description)) AS location_description,
    arrest,
    domestic,
    district,
    community_area,
    latitude,
    longitude,
    year,
    NOW()                         AS loaded_at

FROM raw.raw_chicago_crimes

WHERE
    primary_type IS NOT NULL
    AND latitude  IS NOT NULL
    AND longitude IS NOT NULL
    AND latitude  BETWEEN 41.6  AND 42.1
    AND longitude BETWEEN -87.95 AND -87.5;
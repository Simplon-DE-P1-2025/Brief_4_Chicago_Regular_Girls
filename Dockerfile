# Utilisation de l'image de base Astro Runtime
FROM quay.io/astronomer/astro-runtime:12.6.0

USER root

# Configuration de uv
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1
ENV UV_SYSTEM_PYTHON=1 

# Installation du binaire uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Dépendances système pour Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# On prépare les fichiers
COPY pyproject.toml uv.lock ./

# CORRECTION : Installation propre via uv
# On installe les dépendances listées dans le pyproject.toml
# On ajoute OpenLineage >= 1.8.0 explicitement pour éviter le bug de compatibilité
RUN uv pip install --no-cache -r pyproject.toml "apache-airflow-providers-openlineage>=1.8.0"

# On repasse sur l'utilisateur astro
USER astro
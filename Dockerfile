# Utilisation de l'image de base Astro Runtime
FROM quay.io/astronomer/astro-runtime:12.7.1

# 1. Passer en root pour les installations système
USER root

# 2. Configuration de uv (selon docs.astral.sh)
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1
# Empêche uv de créer un venv, on installe directement dans le système de l'image
ENV UV_SYSTEM_PYTHON=1 

# 3. Installation du binaire uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. Dépendances système pour Postgres (libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 5. Repasser sur l'utilisateur astro pour la sécurité
# 6. Installation des dépendances Python
# On copie d'abord uniquement les fichiers de dépendances pour optimiser le cache Docker
COPY pyproject.toml uv.lock ./

# Installation via uv
# On utilise --no-cache pour réduire la taille de l'image finale
RUN uv pip install --no-cache -r pyproject.toml
USER astro

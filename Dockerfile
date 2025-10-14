FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIPENV_VENV_IN_PROJECT=1 \
    DEBIAN_FRONTEND=noninteractive \
    DJANGO_SUPERUSER_PASSWORD=pass \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1

ENV GUN_DATA_UPDATE_DATE_STRING="Février 2025" \
    GISTRID_DATA_UPDATE_DATE_STRING="Février 2025" \
    RNDTS_DATA_UPDATE_DATE_STRING="Novembre 2024" \
    ADMIN_SLUG="admin" \
    MESSAGE_RECIPIENTS="bill@example.com,sandy@example.com"

RUN apt-get update && apt-get install -y \
     locales \
    # PostgreSQL client
    postgresql-client \
    # Librairies géographiques pour Django (GDAL et GEOS)
    gdal-bin \
    tzdata \
    libgdal-dev \
    libgeos-dev \
    # Autres dépendances
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    curl \
    git \
    netcat-openbsd \
    # Node.js et npm pour le frontend
    nodejs \
    npm

RUN sed -i '/fr_FR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen fr_FR.UTF-8  \
     && rm -rf /var/lib/apt/lists/*

ENV LC_ALL=fr_FR.UTF-8 \
    LANG=fr_FR.UTF-8

# Install uv
ADD --chmod=755 https://astral.sh/uv/install.sh /tmp/install-uv.sh
RUN /tmp/install-uv.sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    cp /root/.local/bin/uvx /usr/local/bin/uvx

RUN useradd -m -r apppuser && \
    mkdir -p /app && \
    chown -R apppuser /app

WORKDIR /app


# Copy uv project files
COPY --chown=apppuser pyproject.toml ./
COPY --chown=apppuser uv.lock ./


# Install dependencies with uv sync
# --frozen ensures we use exact versions from uv.lock
# --no-install-project skips installing the project itself (just deps)
RUN uv sync --frozen --no-install-project

COPY --chown=apppuser:apppuser . .

# Now install the project itself
RUN uv sync --frozen


COPY --chown=apppuser:apppuser docker-entrypoint.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER apppuser
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
WORKDIR /app/src

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000", "--settings", "config.settings.docker"]
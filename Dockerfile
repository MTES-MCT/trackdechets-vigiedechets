FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIPENV_VENV_IN_PROJECT=1 \
    DEBIAN_FRONTEND=noninteractive \
    DJANGO_SUPERUSER_PASSWORD=pass \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    BROWSER_PATH=/usr/bin/chromium

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
    # Chromium dependencies for Kaleido 1.2+
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxkbcommon0 \
    # Chromium browser
    chromium \
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

# Verify Chrome is accessible for Kaleido
RUN /usr/bin/chromium --version

# Install Marianne font for Chromium/Kaleido (used in Plotly graphs)
# Convert WOFF2 to TTF using woff2 tool
RUN apt-get update && apt-get install -y fontconfig woff2 && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/share/fonts/truetype/marianne \
    && cd /app/src/static/css/fonts \
    && woff2_decompress Marianne-Regular.woff2 \
    && woff2_decompress Marianne-Bold.woff2 \
    && woff2_decompress Marianne-Medium.woff2 \
    && mv Marianne-Regular.ttf Marianne-Bold.ttf Marianne-Medium.ttf /usr/share/fonts/truetype/marianne/ \
    && fc-cache -f -v

COPY --chown=apppuser:apppuser docker-entrypoint.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER apppuser
EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
WORKDIR /app/src

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000", "--settings", "config.settings.docker"]
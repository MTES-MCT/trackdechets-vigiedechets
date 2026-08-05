#!/bin/bash
set -e

# Attendre que Redis soit disponible (obligatoire pour Celery)
if [ "$SERVICE_TYPE" = "celery" ]; then
    echo "🔧 Celery worker - Attente de Redis..."
    timeout 30 bash -c 'until nc -z redis 6379; do sleep 0.1; done' || true
    echo "Redis est prêt!"
    echo "🔧 Celery worker - Démarrage..."
    exec "$@"
fi

echo "Attente de PostgreSQL..."
timeout 30 bash -c 'until nc -z db 5432; do sleep 0.1; done' || true
echo "PostgreSQL est prêt!"

echo "Attente de Redis..."
timeout 30 bash -c 'until nc -z redis 6379; do sleep 0.1; done' || true
echo "Redis est prêt!"

# Exécuter une seule fois (durée de vie du conteneur)
BOOTSTRAP_FLAG=/tmp/.web_init_done
if [ ! -f "$BOOTSTRAP_FLAG" ]; then
  if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
    echo "Exécution des migrations..."
    uv run python manage.py migrate --noinput
  else
    echo "Migration ignorée (SKIP_MIGRATIONS=1)"
  fi

  if [ "${SKIP_COLLECTSTATIC:-0}" != "1" ]; then
    echo "Collecte des fichiers statiques..."
    uv run python manage.py collectstatic --noinput --clear || true
  else
    echo "collectstatic ignoré (SKIP_COLLECTSTATIC=1)"
  fi

  if [ "${SKIP_SUPERUSER:-0}" != "1" ]; then
    echo "Création du superutilisateur..."
    uv run  python manage.py createsuperuser \
    --noinput \
    --username admin\
    --email admin@test.fr || true
  else
    echo "Création du superutilisateur ignorée (SKIP_SUPERUSER=1)"
  fi

  touch "$BOOTSTRAP_FLAG"
else
  echo "✅ Initialisation déjà effectuée, démarrage rapide du serveur."
fi

exec "$@"
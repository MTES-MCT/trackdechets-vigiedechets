#!/bin/bash
set -e

 if [ "$SERVICE_TYPE" = "celery" ]; then
    echo "🔧 Celery worker - Skip initialization"
    exec "$@"
fi

echo "Attente de PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL est prêt!"

echo "Attente de Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis est prêt!"

echo "Exécution des migrations..."
uv run python manage.py migrate --noinput

echo "Collecte des fichiers statiques..."
uv run  python manage.py collectstatic --noinput --clear || true


echo "Création du superutilisateur..."
uv run  python manage.py createsuperuser \
    --noinput \
    --username admin\
    --email admin@test.fr || true

exec "$@"
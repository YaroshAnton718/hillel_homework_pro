#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

until python -c "
import os
import psycopg

psycopg.connect(
    host=os.environ['POSTGRES_HOST'],
    port=os.environ['POSTGRES_PORT'],
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
).close()
"; do
    sleep 1
done

echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Ensuring integration service account..."
python manage.py ensure_service_user

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."

exec "$@"
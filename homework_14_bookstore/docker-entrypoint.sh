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

echo "Loading data..."
python manage.py loaddata data.json

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django..."

exec python manage.py runserver 0.0.0.0:8000

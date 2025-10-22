#!/bin/bash

# Exit on error
set -e

# Set defaults if not provided
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-airportuser}

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Creating superuser if not exists..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@airport.com').exists():
    User.objects.create_superuser(
        email='admin@airport.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('Superuser created: admin@airport.com / admin123')
else:
    print('Superuser already exists')
END

echo "Starting server..."
exec "$@"

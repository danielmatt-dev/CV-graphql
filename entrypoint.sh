#!/bin/bash

# Ejecutar las migraciones de Django
python manage.py makemigrations
python manage.py migrate

# Iniciar el servidor de Django
exec "$@"

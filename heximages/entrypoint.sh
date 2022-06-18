#!/bin/sh

rm -r $MEDIAFILES_DIR/*

python manage.py flush --no-input
python manage.py migrate

python manage.py createsuperuser --noinput

python manage.py loaddata initial_data.json
python manage.py loaddata dev.json

exec "$@"
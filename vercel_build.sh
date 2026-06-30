#!/usr/bin/env bash

# Install requirements
pip install -r requirements.txt

# Run migrations and collect static files
python backend/manage.py collectstatic --noinput
python backend/manage.py migrate

#!/usr/bin/env bash
# Exit on any error
set -o errexit

# 1. Install production dependencies
pip install -r requirements/production.txt

# 2. Collect static files (compiles your Tailwind/JS static assets)
python manage.py collectstatic --no-input

# 3. Apply database migrations to your Neon database
python manage.py migrate
#!/usr/bin/env bash
# Exit on any error
set -o errexit

# 1. Install production dependencies
pip install -r requirements/production.txt

# 2. Collect static files (compiles your Tailwind/JS static assets)
python manage.py collectstatic --no-input

# 3. Apply database migrations to your Neon database
python manage.py migrate

# 4. Automatically create your specific ABIS admin superuser
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='ABIS_Admin').exists():
    User.objects.create_superuser('ABIS_Admin', 'aquilabritishsch@gmail.com', 'Sunshine2131@ABIS');
    print('Superuser ABIS_Admin created successfully.')
else:
    print('Superuser ABIS_Admin already exists.')
"
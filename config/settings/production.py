import os
import dj_database_url
from .base import *

# Pull secure production credentials from Render environment variables
SECRET_KEY = os.getenv('SECRET_KEY')

# Allow DEBUG to be turned on locally via environment variables, defaulting to False
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allow traffic from all Render web domains
ALLOWED_HOSTS = ['*']

# Whitenoise Middleware inserted after SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configure database dynamically (handles SQLite locally vs Neon PostgreSQL in production)
db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith('sqlite'):
    DATABASES = {
        'default': dj_database_url.config(
            default=db_url,
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            ssl_require=True
        )
    }

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Override Email Backend to use SMTP in production safely via os.getenv
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
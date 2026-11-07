import os
import dj_database_url
from .base import *

# Dynamically set DEBUG: True for local development, False if explicitly production
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allow local or all hosts depending on environment
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '127.0.0.1:8000', '*']

# Configure database dynamically: handles SQLite locally vs Neon PostgreSQL seamlessly
db_url = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')

if not db_url or db_url.startswith('sqlite'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            ssl_require=True
        )
    }

# Whitenoise Middleware inserted after SecurityMiddleware
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Safe email backend fallback for local testing (uses console if not configured)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
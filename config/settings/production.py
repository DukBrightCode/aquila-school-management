import os
import dj_database_url
from .base import *

# Pull secure production credentials from Render environment variables
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False

# Allow traffic from all Render web domains
ALLOWED_HOSTS = ['*']

# Whitenoise Middleware inserted after SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configure database for Neon PostgreSQL using Render's DATABASE_URL environment variable
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Override Email Backend to use SMTP in production safely via os.getenv
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
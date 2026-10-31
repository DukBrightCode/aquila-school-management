# Python Requirements Reference

## `requirements/base.txt`

- Django 6.1.1 — web framework
- python-decouple — environment/configuration
- psycopg[binary] — PostgreSQL / psycopg3
- whitenoise — production static-file serving
- django-widget-tweaks — template form customization
- Pillow — image uploads and processing
- xhtml2pdf — PDF generation

## `requirements/development.txt`

Includes `base.txt` plus:
- django-debug-toolbar — development/debugging

## `requirements/production.txt`

Includes `base.txt` plus:
- gunicorn — production WSGI server

## Not in `requirements.txt`

- python-dotenv
- psycopg2-binary
- weasyprint
- Tailwind CSS/PostCSS/autoprefixer
- Chart.js

# Aquila British International School Management System

AI-agnostic Django project scaffold based on the master development specification.

## Architecture

- `apps/core` owns the public home page and global school configuration.
- The Admin Dashboard exposes a **Settings** button.
- The admin navigation exposes **Settings** only to ADMIN users.
- The canonical Settings URL is `core:settings`.
- Database-backed `SiteSettings` allows school identity/branding to change without editing
  `.env` or restarting the server.
- Operational data stays in its domain apps.

## Python requirements

```bash
pip install -r requirements/development.txt
```

Shared runtime requirements include Django 6.1.1, python-decouple, psycopg3, WhiteNoise,
django-widget-tweaks, Pillow, and xhtml2pdf.

Tailwind/PostCSS/autoprefixer are managed through `package.json`. Chart.js is loaded from
the dashboard CDN and is not a Python dependency.

## Initial setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements/development.txt
npm install
npm run build
python manage.py migrate
python manage.py runserver
```

Replace the placeholder images in `static/src/images/` with the real school assets.

Follow `Aquila_AI_Agnostic_Development_Specification_Updated_v3.md` stage by stage.

## Academics configuration

Assessment components are term-specific and administrator-configurable. The application does not hard-code CA1, CA2, Exam, fixed maximum scores, or fixed weights. Active assessment weights must total exactly 100% before a term result can be calculated.

# GymTracking Development Guide

## Workflow
- **Always work on `develop` branch** for new features and fixes
- Use feature branches off `develop` if needed for complex work
- Submit manual MR to `main` when ready for production
- **Never commit directly to `main`**

## Tech Stack
- Django 4.2 + Python 3
- SQLite/PostgreSQL
- Tailwind CSS + Chart.js
- Google Fit OAuth2 (no external dependencies)

## Key Features
- Session logging with exercise-set level granularity
- Google Fit integration for workout syncing
- Progress tracking (strength gains, volume trends, personal records)
- Role-based access (athlete/supervisor/superuser)

## Database & State
- Run migrations before testing: `python manage.py migrate`
- Bootstrap DB: `python manage.py bootstrap`

## Code Style
- Keep changes minimal and focused
- No speculative abstractions or over-engineering
- Add comments only where logic isn't self-evident
- Don't add docstrings/type hints unless changing existing patterns

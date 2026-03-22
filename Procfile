release: python manage.py migrate --noinput && python manage.py create_default_superuser
web: gunicorn gymtracking.wsgi --log-file -

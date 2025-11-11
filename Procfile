web: uvicorn PerfectTeeth.wsgi:application --host 0.0.0.0 --port 8000
release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn DjangoProject.wsgi
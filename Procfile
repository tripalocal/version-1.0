web: gunicorn Tripalocal_V1.wsgi --log-file -
worker: celery -A experiences.tasks worker -l info

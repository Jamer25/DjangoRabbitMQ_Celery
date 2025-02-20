import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_docker.settings')

app = Celery('django_docker')

# Usar string para evitar que se serialice la configuración
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks de las apps de Django
app.autodiscover_tasks()

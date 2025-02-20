# myapp/views.py
from django.http import HttpResponse
from .tasks import send_welcome_email

def register(request):
    # Simula la creación de un usuario. En un caso real, aquí procesarías el registro.
    email = "user@example.com"
    
    # Publica la tarea: Django envía la tarea a RabbitMQ y Celery la procesará en segundo plano.
    send_welcome_email.delay(email)
    
    return HttpResponse("Usuario registrado. Se ha encolado el envío del correo de bienvenida.")

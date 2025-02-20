# myapp/views.py
from django.http import HttpResponse
from .tasks import send_welcome_email

def register_many(request):
    email = "user@example.com"
    task_ids = []
    # Encola 50 tareas
    for i in range(150):
        result = send_welcome_email.delay(f"{i}-{email}")
        task_ids.append(result.id)
    return HttpResponse(f"Se han encolado 50 tareas: {task_ids}")

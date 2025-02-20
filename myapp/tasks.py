# myapp/tasks.py
from celery import shared_task

@shared_task
def send_welcome_email(email):
    # Aquí simulas el envío de un correo, en un caso real usarías una función para enviar email.
    print(f"Welcome email sent to {email}")
    return f"Email sent to {email}"

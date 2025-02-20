# myapp/urls.py
from django.urls import path
from .views import register_many

urlpatterns = [
    path("register-many/", register_many, name="register_many"),
]

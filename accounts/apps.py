from django.apps import AppConfig
from django.contrib.auth.models import User

class AccountsConfig(AppConfig):
    name = 'accounts'

def ready(self):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@gmail.com",
            password="admin123"
        )


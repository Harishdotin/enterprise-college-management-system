from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@gmail.com",
                password="Asdf@123#"
            )
            self.stdout.write(self.style.SUCCESS("Admin created"))
        else:
            self.stdout.write(self.style.WARNING("Already exists"))
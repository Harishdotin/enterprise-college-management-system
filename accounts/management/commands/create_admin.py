from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@gmail.com",
                "is_staff": True,
                "is_superuser": True,
            }
        )

        user.email = "admin@gmail.com"
        user.set_password("NewPassword@123")   # New password
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS("Admin created"))
        else:
            self.stdout.write(self.style.SUCCESS("Admin password updated"))
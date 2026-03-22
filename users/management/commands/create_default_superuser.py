from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Crea el superusuario por defecto si no existe ninguno'

    def handle(self, *args, **options):
        User = get_user_model()

        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Superusuario ya existe, no se crea ninguno nuevo.')
            return

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@gymtracking.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin1234!')

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(
            self.style.SUCCESS(f'Superusuario "{username}" creado correctamente.')
        )

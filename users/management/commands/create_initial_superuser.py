
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée un superutilisateur s\'il n\'en existe pas déjà un.'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([username, email, password]):
            self.stdout.write(self.style.ERROR(
                "Assurez-vous que les variables d'environnement DJANGO_SUPERUSER_USERNAME, "
                "DJANGO_SUPERUSER_EMAIL, et DJANGO_SUPERUSER_PASSWORD sont définies."
            ))
            return

        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f"Création du superutilisateur '{username}'..."))
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("Superutilisateur créé avec succès."))
        else:
            self.stdout.write(self.style.WARNING(f"Le superutilisateur '{username}' existe déjà. Aucune action n'est nécessaire."))


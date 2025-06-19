from django.contrib.auth import get_user_model
import os

User = get_user_model()

admin_user = os.getenv('ADMIN_USER', '')
admin_email = os.getenv('ADMIN_EMAIL', '')
admin_password = os.getenv('ADMIN_PASSWORD', '')

if admin_user and admin_email and admin_password:
    if not User.objects.filter(username=admin_user).exists():
        User.objects.create_superuser(
            admin_user,
            admin_email,
            admin_password
        )
    print("Superuser créé avec succès !")
else:
    print("Un superuser existe déjà.")
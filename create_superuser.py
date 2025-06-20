import os
import django

# Configure Django avant d'importer les modèles
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yoursocial.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

admin_user = os.getenv('ADMIN_USER', 'admin')
if not User.objects.filter(username=admin_user).exists():
    User.objects.create_superuser(
        admin_user,
        os.getenv('ADMIN_EMAIL', 'admin@example.com'),
        os.getenv('ADMIN_PASSWORD', 'admin')
    )
    print("✅ Superuser créé avec succès")
else:
    print("⚠️ Superuser existe déjà")
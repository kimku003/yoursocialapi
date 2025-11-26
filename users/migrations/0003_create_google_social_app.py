
import os
from django.db import migrations
from django.conf import settings

def create_google_social_app(apps, schema_editor):
    """
    Crée l'objet SocialApp pour Google en production à partir des variables d'environnement.
    """
    Site = apps.get_model('sites', 'Site')
    SocialApp = apps.get_model('socialaccount', 'SocialApp')

    # Ne s'exécute qu'en environnement de production (si la variable d'environnement est définie)
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_secret = os.environ.get('GOOGLE_SECRET')

    if google_client_id and google_secret:
        # On s'assure que le site principal est bien celui de production
        try:
            site = Site.objects.get(domain='yoursocialapi.onrender.com')

            # On vérifie si une application Google n'existe pas déjà pour ce site
            if not SocialApp.objects.filter(provider='google', sites=site).exists():
                google_app = SocialApp.objects.create(
                    provider='google',
                    name='Google',
                    client_id=google_client_id,
                    secret=google_secret,
                )
                google_app.sites.add(site)
        except Site.DoesNotExist:
            # Si le site n'existe pas, on ne fait rien pour éviter une erreur
            pass

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_update_site_domain'),
        ('socialaccount', '0001_initial'), # Dépend de la migration initiale de socialaccount
    ]

    operations = [
        migrations.RunPython(create_google_social_app),
    ]

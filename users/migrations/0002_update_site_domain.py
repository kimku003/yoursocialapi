
from django.db import migrations
from django.conf import settings

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    site = Site.objects.get(id=settings.SITE_ID)
    site.domain = 'yoursocialapi.onrender.com'
    site.name = 'YourSocial API'
    site.save()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        # Add a dependency on the sites app's initial migration
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_site_domain),
    ]

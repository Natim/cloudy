from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_schema_updates"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="profilesettings",
            name="user",
            field=models.OneToOneField(on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

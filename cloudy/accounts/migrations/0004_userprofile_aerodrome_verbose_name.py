from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_profilesettings_user_onetoone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="aerodrom",
            field=models.CharField(blank=True, max_length=70, verbose_name="Aérodrome"),
        ),
    ]

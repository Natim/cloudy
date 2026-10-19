from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("FCL1080", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fcl1080log",
            name="synthetic_time",
            field=models.IntegerField(default=0),
        ),
    ]

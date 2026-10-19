from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcessedStripeEvent",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("event_id", models.CharField(max_length=255, unique=True)),
                ("event_type", models.CharField(max_length=128)),
                ("processed_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Processed Stripe event"},
        ),
    ]

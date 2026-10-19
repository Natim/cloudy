from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("code", models.CharField(max_length=8, unique=True, verbose_name="Code promo")),
                (
                    "reduc_type",
                    models.CharField(
                        choices=[("P", "percentage discount"), ("M", "miles")],
                        max_length=1,
                        verbose_name="Type",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("discount_value", models.IntegerField(verbose_name="Réduction")),
                ("validity_end", models.DateTimeField(verbose_name="Date de fin")),
                ("used", models.BooleanField(default=False, verbose_name="Usagé")),
                ("number_of_users", models.IntegerField(default=1, verbose_name="Utilistaeurs")),
                ("users", models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Coupon"},
        ),
    ]

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="NoticeType",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("label", models.CharField(max_length=50)),
                ("display", models.CharField(max_length=100)),
                ("description", models.CharField(max_length=100)),
                ("default", models.IntegerField(db_column="default")),
            ],
            options={"db_table": "notification_noticetype"},
        ),
        migrations.CreateModel(
            name="NoticeSetting",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("medium", models.CharField(default="1", max_length=1)),
                ("send", models.BooleanField(default=False)),
                (
                    "notice_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="notification.noticetype",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "notification_noticesetting",
                "unique_together": {("user", "notice_type", "medium")},
            },
        ),
        migrations.CreateModel(
            name="Notice",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("message", models.TextField()),
                ("added", models.DateTimeField(auto_now_add=True)),
                ("unseen", models.BooleanField(default=True)),
                ("archived", models.BooleanField(default=False)),
                ("on_site", models.BooleanField(default=False)),
                (
                    "notice_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="notification.noticetype",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_notices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_notices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "notification_notice", "ordering": ["-added"]},
        ),
        migrations.CreateModel(
            name="ObservedItem",
            fields=[
                (
                    "id",
                    models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("added", models.DateTimeField(auto_now_add=True)),
                ("signal", models.TextField()),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "notice_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="notification.noticetype",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "notification_observeditem"},
        ),
    ]

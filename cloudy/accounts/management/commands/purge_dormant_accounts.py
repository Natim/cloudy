from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from cloudy.accounts.models import UserProfile
from cloudy.payment.models import OrderInvoice, PaymentOrder

# Tables left over from apps that no longer exist in this stack (Django 1.4's
# auth.Message, django-impostor, the old stateful django-registration, and
# dj-webmachine). They still carry foreign keys to auth_user, so deleting a user
# fails on them, but Django has no model to cascade through. The plan keeps these
# tables in place for a later cleanup pass, so only the rows belonging to purged
# users are removed here.
LEGACY_USER_REFERENCES = (
    ("auth_message", "user_id"),
    ("impostor_impostorlog", "impostor_id"),
    ("impostor_impostorlog", "imposted_as_id"),
    ("registration_registrationprofile", "user_id"),
    ("webmachine_consumer", "user_id"),
    ("webmachine_token", "user_id"),
)


class Command(BaseCommand):
    help = "Delete dormant accounts (last_login before cutoff) and related data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--before",
            default="2016-09-08",
            help="Delete users whose last_login is strictly before this date (YYYY-MM-DD).",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--prune-media",
            action="store_true",
            help="Also delete media files referenced by deleted users.",
        )
        parser.add_argument("--batch-size", type=int, default=200)

    def handle(self, *args, **options):
        cutoff = datetime.strptime(options["before"], "%Y-%m-%d")
        if settings.USE_TZ:
            cutoff = timezone.make_aware(cutoff, timezone.get_default_timezone())
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        # Q(...) | Q(...) so that being either staff or a superuser is enough to be
        # spared; exclude(is_staff=True, is_superuser=True) would only protect
        # accounts that are both.
        doomed = User.objects.filter(last_login__lt=cutoff).exclude(Q(is_staff=True) | Q(is_superuser=True))
        total = doomed.count()
        self.stdout.write(f"Users to delete: {total} (cutoff {options['before']})")

        if dry_run:
            self.stdout.write(
                f"Payment orders affected: {PaymentOrder.objects.filter(user__in=doomed).count()}"
            )
            return

        legacy_refs = self.existing_legacy_references()

        deleted = 0
        while True:
            batch_ids = list(doomed.values_list("id", flat=True)[:batch_size])
            if not batch_ids:
                break
            with transaction.atomic():
                orders = PaymentOrder.objects.filter(user_id__in=batch_ids)
                invoice_ids = list(
                    orders.exclude(invoice_id__isnull=True).values_list("invoice_id", flat=True)
                )
                orders.delete()
                if invoice_ids:
                    OrderInvoice.objects.filter(id__in=invoice_ids).delete()
                UserProfile.objects.filter(user_id__in=batch_ids).delete()
                self.clear_legacy_references(legacy_refs, batch_ids)
                User.objects.filter(id__in=batch_ids).delete()
            deleted += len(batch_ids)
            self.stdout.write(f"Deleted {deleted}/{total}")

        self.stdout.write(self.style.SUCCESS(f"Purge complete: {deleted} users removed"))

    def existing_legacy_references(self):
        """Restrict LEGACY_USER_REFERENCES to tables actually present in this database.

        A database built from scratch by `migrate` (and the sqlite test database)
        has none of these tables, so they must be skipped rather than assumed.
        """
        present = set(connection.introspection.table_names())
        return [(table, column) for table, column in LEGACY_USER_REFERENCES if table in present]

    def clear_legacy_references(self, legacy_refs, user_ids):
        if not legacy_refs:
            return
        ids = list(user_ids)
        with connection.cursor() as cursor:
            for table, column in legacy_refs:
                # "= ANY(%s)" with a list rather than "IN %s" with a tuple: psycopg3
                # adapts a Python tuple to a composite literal, not an IN list.
                cursor.execute(
                    "DELETE FROM %s WHERE %s = ANY(%%s)"
                    % (connection.ops.quote_name(table), connection.ops.quote_name(column)),
                    [ids],
                )

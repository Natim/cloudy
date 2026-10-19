from django.db.models import Q
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from cloudy.core.models import FileModel
from cloudy.logbooks import paginator
from cloudy.logbooks.models import LogBase, LogBookBase
from cloudy.stats.models import Airport

# Sends an e-mail alert whenever an user add or modify a log with an unexisting
# airport code.


@receiver(post_save)
def email_alert_unknown_airport(sender, instance, created, **kwargs):
    # Check this is really a log.
    if issubclass(sender, LogBase):
        attributes = ["airpdep", "airpar"]

        not_found = []

        for attr in attributes:
            value = getattr(instance, attr, None)

            if not value == None:
                query = Q(iata=value) | Q(icao=value)
                if not Airport.objects.filter(query).exists():
                    not_found.append({"attr": attr, "value": value})


# All the following handlers take care of the pagination check. Please note:
# the ugly check is because we can't catch signals bound to parents on children
# actions.
# Please see http://code.djangoproject.com/ticket/9318


@receiver(pre_save)
def invalidate_cache_pagination_change(sender, instance, **kwargs):
    # We have to check that it's really a log which triggered the signal
    if issubclass(sender, LogBase):
        # Make sure to normalize the date
        year = instance.date.year
        month = instance.date.month
        day = instance.date.day
        instance.date = instance.cdate.replace(year, month, day)

        # Grab the unmodified version from the database
        try:
            unmodified_object = sender.objects.get(pk=instance.pk)

            # Compare the two dates and the delete flag
            if not unmodified_object.date == instance.date or (
                not unmodified_object.deleted == instance.deleted
            ):
                # Delete the pagination cache.
                paginator.clear_cache(instance.lbook)

        except sender.DoesNotExist:
            paginator.clear_cache(instance.lbook)


@receiver(pre_save)
def update_delete_status_attached_files(sender, instance, **kwargs):
    """
    When we delete a log, make sure all the attached files are marked as
    deleted. Same when undeleted.
    """
    if issubclass(sender, LogBase):
        try:
            unmodified_object = sender.objects.get(pk=instance.pk)
            if not unmodified_object.deleted == instance.deleted:
                state = instance.deleted
                filters = {
                    "owner": instance.lbook.ownr,
                    "deleted": not state,
                }
                failing_files = FileModel.objects.filter(**filters)
                for fo in failing_files:
                    fo.deleted = state
                    fo.save()

        except sender.DoesNotExist:
            return  # Avoid problems with fixtures.


@receiver(post_save)
def invalidate_cache_pagination_add(sender, instance, created, **kwargs):
    # We have to check that it's really a log which triggered the signal
    if issubclass(sender, LogBase):
        # We check if its the creation of the log
        if created == True:
            # Delete the pagination cache
            paginator.clear_cache(instance.lbook)


@receiver(pre_delete)
def invalidate_cache_pagination_delete(sender, instance, **kwargs):
    # We have to check that it's really a log which triggered the signal
    if issubclass(sender, LogBase):
        paginator.clear_cache(instance.lbook)


# Now take care of the totals invalidation
@receiver(post_save)
def invalidate_cache_totals_change(sender, instance, created, **kwargs):
    # We have to check that it's really a log which triggered the signal
    if issubclass(sender, LogBase):
        instance.lbook.invalidate_totals_cache()


@receiver(pre_save)
def invalidate_cache_totals_reports(sender, instance, **kwargs):
    # We have to check that it's really a log which triggered the signal
    if issubclass(sender, LogBookBase):
        # If the logbook is being created, we are sure we have nothing in the
        # cache.
        if not instance.id:
            return

        # Grab the unmodified version from the database
        try:
            unmodified_object = sender.objects.get(id=instance.id)

            # Compare the two reports
            if not unmodified_object.reports == instance.reports:
                # Delete the cache
                instance.invalidate_totals_cache()

        except sender.DoesNotExist:
            # failsafe for fixtures
            return


# Take care of the maps cache
@receiver(post_save)
def invalidate_cache_map_change(sender, instance, created, **kwargs):
    if issubclass(sender, LogBase):
        instance.lbook.invalidate_map_cache()

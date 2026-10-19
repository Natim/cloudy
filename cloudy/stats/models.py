# System imports {{{
import json
from datetime import datetime

# }}}
# Django imports {{{
from django.conf import settings
from django.db import models

# }}}
# Third-party apps {{{
from redis import Redis

# }}}
# Cloudy {{{
from cloudy.core.utils import dict_to_string, time_slice_to_string, traversal

# }}}


redis = Redis(**settings.CONSTANCE_REDIS_CONNECTION)


class Airport(models.Model):
    iata = models.CharField(max_length=10)
    icao = models.CharField(max_length=10)
    location = models.CharField(max_length=200)
    airport = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    coordinates_lat = models.CharField(max_length=20)
    coordinates_lng = models.CharField(max_length=20)

    def coordinates(self):
        return [self.coordinates_lat, self.coordinates_lng, self.airport]

    def __unicode__(self):
        return f"{self.icao} - {self.airport}"


class StatsModelBase(models.Model):
    # Methods to inherit {{{
    def totals_rules(self):
        """
        Override me!
        Returns the rules to compute totals.

        This is a method and not an attribute because mongoengine converts
        every single attribute to database, and we absolutely do *not* need to
        store rule sets in database.
        """

        print("*WARNING* You should override this method.")

        return []

    def home_page_totals(self):
        """
        Return the list of totals to grab for the home page.
        """

        print("*WARNING* You should override this method.")

        return []

    # }}}
    # Methods {{{

    def active_logs(self, time_slice=(None, None), filters={}):
        """
        Active logs
        """
        my_filters = {"deleted": False, "visbl": True}
        my_filters.update(filters)
        return self.logs_qs(time_slice=time_slice, filters=my_filters)

    def save(self, **kwargs):
        """
        Update the update datetime
        """
        self.update = datetime.now()
        super().save(**kwargs)

    def _invalidate_a_cache(self, name):
        """
        As all keys for cache are built on the model of
            (cache_name):(logbook_id):stuff
        we can delete them with a single function.
        Note: This is a costly operation.
        """
        if settings.CACHING:
            keys = redis.keys(f"{name}:{self.id}:*")
            # for key in keys.split():
            for key in keys:
                redis.delete(key)

    def invalidate_map_cache(self):
        self._invalidate_a_cache("map")

    def invalidate_totals_cache(self):
        self._invalidate_a_cache("total")

    def get_totals(self, totals, time_slice=(None, None), filters={}, group_by=None, reports=True):
        """
        Totals computation. Basically the heart of the stats.
        """

        # We create a dictionary to store results.
        results = {}

        # We make a new list to track totals which will need to be computed.
        # Note: we use list() in order to make a copy of the provided list, so
        # as we avoid references problems.
        to_be_computed = list(totals)

        # If we have to cache something
        if settings.CACHING:
            # For each requested total, we test if it has a cached version
            for total in totals:
                # First we forge the Redis key
                key_values = {
                    "logbook_id": self.id,
                    "str_timeslice": time_slice_to_string(time_slice),
                    "total": total,
                    "filters": dict_to_string(filters),
                    "reports": reports,
                    "group_by": group_by,
                }
                key = (
                    "total:%(logbook_id)s:%(total)s:%(str_timeslice)s:%(filters)s:%(reports)s:%(group_by)s"
                    % key_values
                )

                # And we grab the result
                cached_total = redis.get(key)

                # If something is cached
                if cached_total is not None:
                    # We parse the JSON result. It will always be the exact
                    # same:
                    #
                    # {
                    #   "__sum__": 100,
                    #   "avion1": 65,
                    #   "avion2": 35
                    # }
                    res = json.loads(cached_total)

                    # If we only have one key in the dict, it means that the
                    # result has not been computed for the group_by request.
                    # So if the request asks for group_by, we can't continue.
                    if not ((group_by is not None) and (len(res.keys()) == 1)):
                        # Looks good, we can push the results and invalidate
                        # the total.
                        to_be_computed.remove(total)

                        if group_by is not None:
                            results[total] = res
                        else:
                            # results[total] = res['__sum__']
                            if res.__class__ == dict:
                                results[total] = int(res["__sum__"])
                            else:
                                results[total] = int(res)

        # If we still have something to compute, grab the logs
        logs = []
        if len(to_be_computed) > 0:
            logs = self.logs_qs(time_slice, filters)
        # First, if asked, we apply the reports
        reports_dict = {}
        if reports is True:
            # Grab the reports from the logbook:
            reports_dict = getattr(self, "reports", {})
            if reports_dict is None:
                reports_dict = {}

        full_rules = self.totals_rules()

        # Now for something completely different, here is the real
        # computation job.
        for total in to_be_computed:
            local_res = {"__sum__": 0}

            rules = full_rules[total]

            if reports is True:
                for rule in rules:
                    # local_res["__sum__"] += reports_dict.get(rule.replace(".", "__"), 0)
                    pass  # TODO

            i = -1
            for log in logs:
                i += 1
                if group_by is not None:
                    group_by_value = traversal(log, group_by)
                    if group_by_value not in local_res.keys():
                        local_res[group_by_value] = 0

                for rule in rules:
                    val = traversal(log, rule)
                    if not val:
                        val = 0
                    local_res["__sum__"] += int(val)

                    if not group_by == None:
                        local_res[group_by_value] += int(val)

            if not group_by == None:
                results[total] = local_res
            else:
                results[total] = local_res["__sum__"]

        # Once the computation is done, we store (if asked to) the results in
        # Redis.
        if settings.CACHING == True:
            for total in to_be_computed:
                # First we forge the Redis key
                key_values = {
                    "logbook_id": self.id,
                    "str_timeslice": time_slice_to_string(time_slice),
                    "total": total,
                    "filters": dict_to_string(filters),
                    "reports": reports,
                    "group_by": group_by,
                }
                key = (
                    "total:%(logbook_id)s:%(total)s:%(str_timeslice)s:%(filters)s:%(reports)s:%(group_by)s"
                    % key_values
                )

                json_to_store = json.dumps(results[total])
                redis.set(key, json_to_store)

        # We did it!
        return results

    # }}}

    class Meta:
        abstract = True

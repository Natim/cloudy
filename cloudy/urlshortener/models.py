import random

import redis
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils.http import int_to_base36


class Link(models.Model):
    """
    Virtual Model using redis
    """

    class Meta:
        # Every short URL lives in redis; this model only groups the helpers below.
        # Without managed = False Django expects an (empty, id-only) table, which is
        # what production ended up with and what made the schema diverge from a
        # from-scratch migrate.
        managed = False

    @classmethod
    def shorten(cls, long_url=None):
        r = redis.Redis(
            host=settings.REDIS_SERVER,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )

        # Check first if the url has been shorten before
        is_url_in_base = r.get("id:%s:url" % long_url)
        print(">>  is_url_in_base ", is_url_in_base)
        if is_url_in_base:
            return is_url_in_base

        url_hash = "%x" % (r.incr("next.url.id") + random.randint(0, 100))

        b36_hash = int_to_base36(int(url_hash, 16))
        # next we store the long_url against this hex key
        r.set("url:%s:id" % b36_hash, long_url)
        r.set("id:%s:url" % long_url, b36_hash)

        # push this new short url in global list of urls
        r.rpush("global:urls", b36_hash)
        return b36_hash

    @classmethod
    def expand(cls, url_hash=None):
        r = redis.Redis(
            host=settings.REDIS_SERVER,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )
        return r.get("url:%s:id" % url_hash)

    @classmethod
    def tiny_url(cls, long_url):
        """Tinyurl"""
        tinyurl = Link.shorten(long_url)
        domain = Site.objects.get_current().domain
        return f"{domain}{reverse('shorturl:expand', kwargs={'b36hash_code': tinyurl})}"

from urllib.parse import quote_plus, unquote_plus

from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect

from .models import Link


def expand_url(request, b36hash_code):
    """
    Return the matching URL
    """
    long_url = Link.expand(b36hash_code)
    if not long_url:
        return HttpResponseRedirect("/")

    # redis hands back bytes unless the client is configured to decode responses.
    if isinstance(long_url, bytes):
        long_url = long_url.decode("utf-8")

    domain = Site.objects.get_current().domain
    prefix = quote_plus(f"http://{domain}/")
    uri = long_url.removeprefix(prefix)
    return HttpResponseRedirect("/" + unquote_plus(uri))

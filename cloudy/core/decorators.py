from django.http import HttpResponseBadRequest

from cloudy.core.utils import is_ajax


def ajax_required(f):
    """
    AJAX request required decorator
    http://www.djangosnippets.org/snippets/771/
    """

    def wrap(request, *args, **kwargs):
        if not is_ajax(request):
            return HttpResponseBadRequest()
        return f(request, *args, **kwargs)

    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from django.db.models import Model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

ModelT = TypeVar("ModelT", bound=Model)


def is_ajax(request: HttpRequest) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def get_object_or_None(klass: type[ModelT], /, **kwargs: Any) -> ModelT | None:
    try:
        return klass.objects.get(**kwargs)
    except klass.DoesNotExist:
        return None


def render_to(template_name: str) -> Callable:
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
            context = view_func(request, *args, **kwargs)
            if isinstance(context, HttpResponse):
                return context
            return render(request, template_name, context or {})

        return wrapper

    return decorator


from contextlib import contextmanager
from datetime import datetime
from os import path

from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_dateutil

DATETIME_FORMAT = "%Y-%m-%dT%H-%M-%S-%f"


def encode_datetime(datetime_object, dformat=DATETIME_FORMAT):
    """
    >>> dt_object = datetime(2011, 4, 25, 11, 33, 39, 6100)
    >>> encode_datetime(dt_object)
    '2011-04-25T11-33-39-6100'
    """
    return datetime_object.strftime(dformat)


def decode_datetime(string, dformat=DATETIME_FORMAT):
    """
    >>> time_string = '2011-04-25T11-33-39-6100'
    >>> decode_datetime(time_string)
    datetime(2011, 4, 25, 11, 33, 39, 6100)
    """
    return datetime.strptime(string, dformat)


def time_slice_to_string(time_slice, dformat=DATETIME_FORMAT):
    """
    This function transforms a time slice (ie a couple of datetime objects) to a
    clean string representation.
    We use it in order to store time_slices as keys in the database.
    """

    char = map(lambda x: "None" if x is None else encode_datetime(x, dformat), time_slice)
    tvalues = tuple(char)
    return "%s;%s" % tvalues


def dict_to_string(dictionary):
    """
    Create a nice unique string representation for the given dictionary.

    >>> md = {'a': 4, 'b': 'foo', 'c': 'sample'}
    >>> dict_to_string(md)
    "a=4&b=foo&c=sample"
    """
    string = ""
    keys = sorted(dictionary.keys())
    for key in keys:
        value = dictionary[key]
        string = f"{string}&{key}={value}"
    # We strip the first & if needed
    if len(string) > 0:
        string = string[1:-1]
    return string


def traversal(original_object, path):
    """
    This function grab the attribute at the given path starting from the
    original object.

    >>> class A:
    ...     item1 = "hello"
    >>> class B:
    ...     item2 = A()
    >>> traversal(B(), 'item2.item1')
    "hello"
    """

    base = original_object
    chunks = path.split(".")

    for chunk in chunks:
        try:
            base = getattr(base, chunk)
        except AttributeError:
            base = base[chunk]
    return base


def convert_str_to_date(begin_date, end_date):
    if isinstance(begin_date.__class__, str):
        if begin_date == "none":
            begin_date = None
        else:
            begin_date = parse_dateutil(begin_date, dayfirst=True)
    if isinstance(end_date.__class__, str):
        if end_date == "none":
            end_date = None
        else:
            end_date = parse_dateutil(end_date, dayfirst=True)

    return begin_date, end_date


def apply_multiple_times(func, n, arg):
    """
    Apply n times a function, initially providing it *args.
    Obviously the given function must compose with itself. In maths it's called
    function iteration [1].

    [1] http://en.wikipedia.org/wiki/Iterated_function

    The following use a standard incrementation function to count from zero to
    5:
    >>> apply_multiple_times(lambda x: x+1, 5, 0)
    5

    Another example with string manipulation (paths):
    >>> from os import path
    >>> base = "/foo/bar/hello/world.c"
    >>> apply_multiple_times(path.dirname, 2, base)
    '/foo/bar'
    """

    if n == 1:
        return func(arg)
    else:
        return func(apply_multiple_times(func, n - 1, arg))


def monthdelta(date, delta):
    # FIXME Huh, I'm pretty sure we can avoid this using datetime library.
    month = (date.month + delta) % 12
    year = date.year + ((date.month) + delta - 1) // 12

    if not month:
        month = 12

    day = min(
        date.day,
        [
            31,
            29 if year % 4 == 0 and not year % 400 == 0 else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][month - 1],
    )
    return date.replace(day=day, month=month, year=year)


# I'm not sure this function is still used (because we don't use windmill).
def with_fixtures(fixtures=[]):
    def dec(func):
        def gave(*k, **a):
            import windmill

            old = getattr(windmill, "fixtures", None)
            windmill.fixtures = fixtures
            applied = func(*k, **a)
            if not old == None:
                setattr(windmill, "fixtures", old)
            # call_command('flush')
            return applied

        gave.__name__ = func.__name__
        return gave

    return dec


class SettingDoesNotExist:
    pass


@contextmanager
def patch_settings(**kwargs):
    """
    This decorator allows use to run a snippet of code use different Django
    settings. It's useful in tests when we want to run them in some specific
    conditions.
    """
    from django.conf import settings

    old_settings = []
    for key, new_value in kwargs.items():
        old_value = getattr(settings, key, SettingDoesNotExist)
        old_settings.append((key, old_value))
        setattr(settings, key, new_value)
    yield
    for key, old_value in old_settings:
        if old_value is SettingDoesNotExist:
            delattr(settings, key)
        else:
            setattr(settings, key, old_value)


@contextmanager
def patch_time(old_dtime):
    """
    In this context, the `time` library is monkey patched so that the code will
    run in the specified time.

    >>> import datetime
    >>> old_time = datetime.datetime(1984,1,2)
    >>> with patch_time(old_time):
    ...     from datetime import datetime
    ...     datetime.now().date()
    datetime.date(1984, 1, 2)
    >>> import datetime
    >>> datetime.datetime.now().date() == datetime.datetime(1984, 1, 2).date()
    False
    """

    import datetime

    # Back up the old datetime class
    old = datetime.datetime

    # Create the patched class
    class PatchedDatetime(datetime.datetime):
        @classmethod
        def now(cls):
            # This work because old_time is a datetime object which means it is
            # immutable.
            return old_dtime

    # Monkey patch
    setattr(datetime, "datetime", PatchedDatetime)

    # Run the code
    yield

    # Restore the old datetime
    datetime.datetime = old


def count_files(valid_path):
    """Return the number of files in a folder"""
    from os import listdir

    return len(listdir(valid_path))


def get_valid_name(name):
    from django.template.defaultfilters import slugify
    from django.utils.encoding import smart_str

    n = name.rsplit(".", 1)[0]
    ext = name.rsplit(".", 1)[1]
    n = smart_str(slugify(n).replace("-", "_"))
    return f"{n}.{ext}"


def upload_to(base_name):
    def _upload_to(instance, filename):
        """Return a clean file path to save to. This avoid unicode
        clusterfucking because we remove UTF8 chars."""
        return path.join(base_name(), get_valid_name(filename))

    if isinstance(base_name, str):
        return base_name
    return _upload_to


def contains_html(data, *args, **kwargs):
    """
    Helper for tests to check if the given HTML code contains the described
    element. Use beautiful soup arguments in *args and **kwargs.

    This is a temporary function until
    https://docs.djangoproject.com/en/dev/topics/testing/#django.test.TestCase.assertHTMLEqual
    gets to the stable release.

    Use example:
    contains_html(resp.content, "td", "reports-info", text=re.compile("14:00"))
    """
    soup = BeautifulSoup(data)
    return bool(soup.findAll(*args, **kwargs))

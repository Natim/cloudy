from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter

from cloudy.logbooks.forms import FileCommentsForm
from cloudy.time_format import TIME_MAPPING

register = template.Library()


@register.inclusion_tag("partials/paginator.html", takes_context=True)
def paginator(context, logbook, pages_count, page):
    """
    Compute the list to display on the paginator.
    """
    iteration = []
    next_item = None
    previous = None

    trailing_side = 2

    if pages_count <= 1:
        pass
    elif pages_count <= trailing_side * 2 + 1:
        iteration = range(1, pages_count + 1)

    else:
        after = page + trailing_side
        before = page - trailing_side
        if after > pages_count:
            before -= after - pages_count
            after = pages_count
        elif before < 1:
            after += abs(before) + 1
            before = 1
        iteration = range(before, after + 1)

        if page - 1 > 0:
            previous = before - 1
        if page + 1 <= pages_count:
            next_item = after + 1

    if page + trailing_side >= pages_count:
        next_item = None

    if page - trailing_side <= 1:
        previous = None

    context.update(
        {
            "iteration": iteration,
            "page": page,
            "next": next_item,
            "pages_count": pages_count,
            "previous": previous,
            "logbook": logbook,
        }
    )

    return context


@register.inclusion_tag("popups/add_logbook.html", takes_context=True)
def logbook_popup(context):
    """
    Gen html for add logbook popup
    """
    context.update({"LOG_BOOKS_TYPE": settings.LOG_BOOKS_TYPE})
    return context


@register.inclusion_tag("popups/import.html", takes_context=True)
def import_popup(context):
    """
    Gen html for impoty logbook popup
    """
    form = FileCommentsForm()
    context.update({"form": form})
    return context


@register.inclusion_tag("popups/export.html", takes_context=True)
def export_popup(context):
    """
    Gen html for export logbook popup
    """
    return context


@register.inclusion_tag("popups/add_log.html", takes_context=True)
def addlog_popup(context, logbook):
    """
    Gen html for add log for a particular logbook
    """
    if "show_log_form" in context:
        form = context["show_log_form"]
    else:
        form = logbook._log_form_model()(logbook)
    context.update({"logbook_cat": logbook.cat, "logbook_id": logbook.id, "form": form})
    return context


@register.filter
@stringfilter
def hmin(value, logbook):
    if value in ["0", ""]:
        return ""
    value = int(value)
    return logbook.time_formatter.output(value)


@register.filter
@stringfilter
def height(value, logbook):
    if value in ["0", ""]:
        return ""
    value = int(value)
    return logbook.height_formatter.output(value)


@register.filter
@stringfilter
def hmin_hhmm(value, logbook):
    """
    Force hh:mm format
    """
    if value in ["0", ""]:
        return ""
    value = int(value)
    return TIME_MAPPING[0][1].output(value)


@register.filter
@stringfilter
def hmin_hour(value, logbook):
    if value in ["0", ""]:
        return ""
    value = int(value)
    return _split_hmin(logbook.time_formatter.output(value), True)


@register.filter
@stringfilter
def hmin_min(value, logbook):
    if value in ["0", ""]:
        return ""
    value = int(value)
    return _split_hmin(logbook.time_formatter.output(value), False)


def _split_hmin(original_hmin_str, left=True):
    if ":" in original_hmin_str:
        bits = original_hmin_str.split(":")
    else:
        bits = original_hmin_str.split(".")
    if left:
        return bits[0]
    return bits[1]


@register.filter
@stringfilter
def hour_part(value):
    return _splitter_helper(value, 0)


@register.filter
@stringfilter
def min_part(value):
    return _splitter_helper(value, 1)


def _splitter_helper(value, pos):
    spliters = [":", "."]
    for splitter in spliters:
        if splitter in value:
            return value.split(splitter)[pos]
    return ""


@register.filter
def nth(sequence, index):
    """Return sequence[index], or None if the index is out of range."""
    try:
        return sequence[int(index)]
    except IndexError, TypeError, ValueError:
        return None


@register.filter
def truncchar(value, arg):
    """Truncate after a certain number of characters."""
    if not value:
        return value
    if len(value) < arg:
        return value
    return value[:arg] + "..."

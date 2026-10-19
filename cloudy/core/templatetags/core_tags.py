import re

# from notification.models import Notice
from constance import config
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def get_config_var(name):
    return getattr(config, name)


# @register.inclusion_tag('partials/unseen_noticies.html')
# def show_unseen_noticies_for_user(user):
#     """
#     Display unseen noticies for a given user
#     """
#     noticies = []
#     if not user.is_anonymous():
#         noticies = Notice.objects.notices_for(user, unseen=True)
#     return {'noticies': noticies}


@register.inclusion_tag("popups/firstclass_only.html", takes_context=True)
def firstclass_only_popup(context):
    return context


@register.inclusion_tag("popups/firstclass_only_stats.html", takes_context=True)
def firstclass_only_popup_stats(context):
    return context


@register.inclusion_tag("popups/hiddenlogbook.html", takes_context=True)
def hiddenlogbook_popup(context):
    return context


@register.filter
def sexy_me(value):
    return re.sub(r"\[(.+)\]", "", value)


@register.filter
def nth(lst, number):
    val = None
    try:
        val = lst[number]
    except IndexError:
        pass
    return val


@register.inclusion_tag("partials/snapabug.html")
def snapabug():
    return {"debug": settings.DEBUG, "widgetid": settings.SNAPABUG_WIDGETID}


_GA_PROPERTY_ID = re.compile(r"^UA-\d+-\d+$")
_GAUGES_SITE_ID = re.compile(r"^[0-9a-fA-F]+$")
_GAUGES_SNIPPET = """<script type="text/javascript">
    var _gauges = _gauges || [];
    (function () {
      var t = document.createElement('script');
      t.type = 'text/javascript';
      t.async = true;
      t.id = 'gauges-tracker';
      t.setAttribute('data-site-id', '%s');
      t.src = '//secure.gaug.es/track.js';
      var s = document.getElementsByTagName('script')[0];
      s.parentNode.insertBefore(t, s);
    })();
    </script>"""


@register.simple_tag(takes_context=True)
def google_analytics(context):
    """Render Universal Analytics only when a property id is configured."""
    property_id = getattr(settings, "GOOGLE_ANALYTICS_PROPERTY_ID", "") or ""
    if not _GA_PROPERTY_ID.fullmatch(property_id):
        return ""
    from analytical.templatetags.google_analytics import GoogleAnalyticsNode

    return mark_safe(GoogleAnalyticsNode().render(context))


@register.simple_tag
def gauges():
    """Render the Gauges tracker only when a site id is configured."""
    site_id = getattr(settings, "GAUGES_SITE_ID", "") or ""
    if not _GAUGES_SITE_ID.fullmatch(site_id):
        return ""
    return mark_safe(_GAUGES_SNIPPET % site_id)


class PercentEvolNode(template.Node):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def render(self, context):
        a = context[self.a]
        b = context[self.b]
        if a == 0 or b == 0:
            return "0"
        if a == b:
            return "0"
        if a < b:
            return "%s" % (int(100.0 / a * b) - 100)
        return "%s" % (int(100.0 / b * a) - 100)


def do_percent_progress(parser, token):
    """
    USE:
        {% percent_evol a b %}
    """

    res = token.split_contents()
    if not len(res) == 3:
        raise template.TemplateSyntaxError("%r tag misuse" % token.contents.split())
    return PercentEvolNode(res[1], res[2])


register.tag("percent_evol", do_percent_progress)

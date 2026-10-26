from django import template

register = template.Library()


@register.inclusion_tag("popups/date_selector.html", takes_context=True)
def date_selector_popup(context):
    """
    Gen html for add logbook popup
    """
    return context


# Format Total
# Grab a total from a total dict and display it.
class FormatTotalNode(template.Node):
    def __init__(self, totals, total_name, formatting):
        self.totals = template.Variable(totals)
        self.total_name = total_name
        self.formatting = formatting

    def render(self, context):
        totals = self.totals.resolve(context)
        value = int(totals.get(self.total_name, 0))

        if self.formatting == "dontformat":
            if value == 0:
                return ""
            return str(value)
        if self.formatting == "raw":
            return str(value)

        formatted = context["logbook"].time_formatter.output(int(value))

        if self.formatting == "report":
            if value == 0:
                return ""
            else:
                return formatted

        elif self.formatting == "height":
            return context["logbook"].height_formatter.output(int(value), decorated=True)

        elif self.formatting == "decorated":
            return context["logbook"].time_formatter.output(int(value), decorated=True)

        elif self.formatting == "plain":
            return formatted

        # When in doubt
        return ""


def do_format_total(parser, token):
    """
    USE:
        {% format_total totals total_name formatting %}
    """

    res = token.split_contents()
    if not len(res) == 4:
        raise template.TemplateSyntaxError("%r tag misuse" % token.contents.split())
    return FormatTotalNode(res[1], res[2], res[3])


register.tag("format_total", do_format_total)


class FormatTotalAsNode(template.Node):
    """
    Same as formatTotal but set the result as a context var
    accessible to our template
    """

    def __init__(self, totals, total_name, formatting, context_target):
        self.totals = template.Variable(totals)
        self.total_name = total_name
        self.formatting = formatting
        self.context_target = context_target

    def render(self, context):
        totals = self.totals.resolve(context)
        value = int(totals.get(self.total_name, 0))
        context_target = self.context_target
        if self.formatting == "dontformat":
            if value == 0:
                value = ""
            context[context_target] = value
            return ""

        formatted = context["logbook"].time_formatter.output(int(value))

        if self.formatting == "report":
            if value == 0:
                context[context_target] = ""
                return ""
            else:
                context[context_target] = formatted
                return ""

        elif self.formatting == "decorated":
            result = context["logbook"].time_formatter.output(int(value), decorated=True)
            context[context_target] = result
            return ""
        # When in doubt
        context[context_target] = ""
        return ""


def do_format_total_as(parser, token):
    """
    USE:
        {% do_format_total_as totals total_name formatting as foo%}
    """

    res = token.split_contents()
    if not len(res) == 6:
        raise template.TemplateSyntaxError("%r tag misuse" % token.contents.split())
    return FormatTotalAsNode(res[1], res[2], res[3], res[5])


register.tag("format_total_as", do_format_total_as)

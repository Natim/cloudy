"""
# Time_format Formatters

Formatters wrap the basic conversion operations:

    - min -> custom format
    - custom format -> min
"""


class BaseFormatter:
    @staticmethod
    def output(nbr_minutes, **kwargs):
        """
        The output method does the (min -> custom format) conversion.
        """
        raise NotImplementedError

    @staticmethod
    def input(custom_format, **kwargs):
        """
        The input method does the (custom format -> min) conversion.
        """
        raise NotImplementedError


class HhmmFormatter(BaseFormatter):
    """
    This is the default display, the European way.
    """

    @staticmethod
    def output(nbr_minutes, **kwargs):
        # Ensure minutes is an integer, so we can use euclidean division.
        minutes = int(nbr_minutes)
        hours = minutes // 60
        minutes = minutes % 60

        if minutes < 10:
            minutes = "0%s" % minutes

        if kwargs.get("decorated"):
            return f"<span class='hour_num'>{hours}</span>\
                    <span class='hour'>H</span>\
                    <span class='min_num'>{minutes}</span>\
                    <span class='min'>M</span>"

        return f"{hours}:{minutes}"

    @staticmethod
    def input(custom_format, **kwargs):
        hh, mm = custom_format.split(":")
        hours = 0
        try:
            hours = int(hh)
        except Exception:
            pass

        if mm == "None":
            mm = 0
        minutes = int(mm)

        return minutes + 60 * hours


class TenthFormatter(BaseFormatter):
    """
    Display play the US way, using tenths.
    """

    @staticmethod
    def output(nbr_minutes, **kwargs):
        # In Python, if you want to do a float division, you have to involve
        # floats in the calculus: if you only use two integers, the interpreter
        # will perform an euclidean division (which will not return the decimal
        # part).  That's why we divide by 60.0 instead of 60.
        #
        # Also, the `round` function only round to the nearest integer (yet if
        # you round a float it will remain a float after the rounding), so we
        # multiply by 10, round, then divide by 10, so we actually performed
        # a rounding at 10^-1.

        result = str(round(nbr_minutes / 60.0 * 10) / 10)
        if kwargs.get("decorated"):
            return "<span class='hour_num'>%s</span>" % result
        return result

    @staticmethod
    def input(custom_format, **kwargs):
        # We are sure we will parse an integer because custom_format >= 0.1.
        return int(float(custom_format) * 60)


class CanadianFormatter(BaseFormatter):
    # TODO https://github.com/coulix/cloudy/issues/146#issuecomment-1545494
    pass

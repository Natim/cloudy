"""Normalize FCL 1.080 places to ICAO (OACI) codes."""

import re

_ICAO_RE = re.compile(r"^[A-Za-z0-9]{4}$")


def icao_from_place(place: str | None) -> str:
    """Return the ICAO code from a place string, or the original if none is found.

    Autocomplete historically stored ``LFRN - Rennes Saint Jacques``.
    """
    if not place:
        return ""
    place = place.strip()
    head = place.split(" - ", 1)[0].strip()
    token = head.split()[0] if head else ""
    if _ICAO_RE.fullmatch(token):
        return token.upper()
    return place

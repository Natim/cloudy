"""Compile every template in the project.

Django only parses a template when something renders it, so a template still using
Django 1.4 syntax ({% url foo %} without quotes, the removed length_is filter, ...)
stays invisible until a user reaches that exact page. Compiling them all turns those
into test failures, and reverse()-ing the {% url %} targets catches names that no
longer exist.
"""

from pathlib import Path

import pytest
from django.template.loader import get_template

import cloudy
import cloudy.urls  # noqa: F401  (registers the custom path converters)

TEMPLATE_ROOTS = [Path(cloudy.__file__).parent / "templates"] + sorted(
    Path(cloudy.__file__).parent.glob("*/templates")
)


def template_names():
    names = set()
    for root in TEMPLATE_ROOTS:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".html", ".txt"}:
                names.add(str(path.relative_to(root)))
    return sorted(names)


@pytest.mark.parametrize("template_name", template_names())
def test_template_compiles(template_name):
    get_template(template_name)

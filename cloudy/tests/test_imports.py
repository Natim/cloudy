"""Import every module in the project.

Much of this codebase imports forms, widgets and helpers lazily from inside view
and model methods, so `manage.py check` and the rest of the suite can pass while a
module still carries a Django 1.4-era import that raises the moment a user hits the
page. Importing everything up front turns those latent failures into test failures.
"""

import importlib
import pkgutil

import pytest

import cloudy

# Importing the root URLconf registers the custom path converters that the per-app
# urls modules reference, so it has to happen before they are imported.
import cloudy.urls  # noqa: F401


def project_modules():
    return sorted(
        module.name
        for module in pkgutil.walk_packages(cloudy.__path__, prefix="cloudy.")
        if ".migrations" not in module.name
    )


@pytest.mark.parametrize("module_name", project_modules())
def test_module_imports(module_name):
    importlib.import_module(module_name)

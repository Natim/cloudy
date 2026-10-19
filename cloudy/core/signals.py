from django.dispatch import Signal

# Disable the error about the name because it's all about consistency with
# Django signals (wrote in lowercase).
# pylint: disable=C0103
hard_error = Signal()  # sends msg and ctx; providing_args was removed in Django 4.0

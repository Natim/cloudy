# System imports {{{
import os

from django.conf import settings
from django.contrib.auth.models import User

# }}}
# Django imports {{{
from django.db import models

# }}}
# Cloudy {{{
from .utils import upload_to

# }}}
#


class FileModel(models.Model):
    """Model to link multiple files with m2m."""

    # Fields {{{
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)
    cdate = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True, db_column="udate")
    file = models.FileField(upload_to=upload_to("upload"))
    # }}}

    def filename(self):
        return os.path.basename(self.file.name)

    def filesize(self):
        try:
            return self.file.size
        except OSError, ValueError:
            return 0

    def url(self):
        return settings.MEDIA_URL + str(self.file)


# Signals {{{
import sys

from django.core.signals import got_request_exception


def my_callback(sender, **kwargs):
    exc_info = sys.exc_info()
    print("We got an exception", exc_info)


got_request_exception.connect(my_callback)
# }}}

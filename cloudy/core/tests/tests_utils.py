from datetime import datetime

import pytest

from cloudy.core import utils


def test_convert_str_to_date_parses_slash_and_iso_dates():
    begin, end = utils.convert_str_to_date("2025/10/20", "2026-01-02")
    assert begin == datetime(2025, 10, 20)
    assert end == datetime(2026, 1, 2)
    assert utils.convert_str_to_date("20/10/2025", None)[0] == datetime(2025, 10, 20)


def test_convert_str_to_date_keeps_datetimes_and_none():
    begin = datetime(2024, 3, 1, 12, 0)
    assert utils.convert_str_to_date(begin, None) == (begin, None)
    assert utils.convert_str_to_date("none", "none") == (None, None)


def test_get_valid_name():
    filename = "Random_name/Sh1ti+filen&me.JpEg"
    result = utils.get_valid_name(filename)
    waited = "random_namesh1tifilenme.JpEg"
    assert result == waited


def test_upload_to_FilenameIsStr():
    name = "random-filename-png"
    result = utils.upload_to(name)
    assert result == name


def test_upload_to_FilenameIsNotStr():
    assert 1  # TODO


@pytest.mark.django_db
def test_filesize_missing_file_is_zero():
    from django.contrib.auth.models import User
    from django.template import Context, Template

    from cloudy.core.models import FileModel

    user = User.objects.create_user("fileuser", "file@example.com", "secret")
    fo = FileModel.objects.create(owner=user, file="upload/Screenshot_missing.png")
    assert fo.filesize() == 0
    html = Template("{% widthratio file.filesize 1000 1 %} Kb").render(Context({"file": fo}))
    assert html == "0 Kb"

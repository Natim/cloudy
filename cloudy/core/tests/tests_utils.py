import pytest

from cloudy.core import utils


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

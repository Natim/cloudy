from django.contrib.auth.models import User
from django.test import TestCase

from cloudy.accounts.models import _avatar_path, UserProfile
from cloudy.DGAC_avion_logbook.models import DGACAvionLogBook
from cloudy.DGAC_planeur_logbook.models import DGACPlaneurLogBook


class UserProfileLogbookTypeTestCase(TestCase):
    def test_has_logbook_of_type(self):
        user = User.objects.create_user("pilot", "pilot@example.com", "secret")
        UserProfile.objects.create(user=user, dob="1990-01-01")
        profile = user.userprofile

        plane = DGACAvionLogBook(ownr=user, name="Avion", cat="plane_dgac")
        plane.save()

        self.assertTrue(profile.has_logbook_of_type("plane_dgac"))
        self.assertFalse(profile.has_logbook_of_type("glider_dgac"))

        glider = DGACPlaneurLogBook(ownr=user, name="Planeur", cat="glider_dgac")
        glider.save()

        self.assertTrue(profile.has_logbook_of_type("glider_dgac"))


def test_avatar_path_accepts_filefield_upload_to_signature():
    name = UserProfile._meta.get_field("avatar").generate_filename(None, "Avatar Photo.JPG")
    assert name.startswith("avatars/")
    assert name.endswith("avatar_photo.JPG")
    assert _avatar_path(None, "avatar.jpg").endswith("avatar.jpg")

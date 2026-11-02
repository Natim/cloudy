from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cloudy.accounts.admin import UserProfileAdmin
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


class UserProfileAdminLogbookLinkTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("pilot", "pilot@example.com", "secret")
        self.profile = UserProfile.objects.create(user=self.user, dob="1990-01-01")
        self.column = UserProfileAdmin(UserProfile, AdminSite())

    def test_links_to_the_visible_logbook(self):
        DGACAvionLogBook(ownr=self.user, name="Hidden", cat="plane_dgac", visbl=False).save()
        active = DGACAvionLogBook(ownr=self.user, name="Active", cat="plane_dgac")
        active.save()
        DGACPlaneurLogBook(ownr=self.user, name="Deleted", cat="glider_dgac", deleted=True).save()

        link = str(self.column.logbooks_link(self.profile))
        url = reverse("logbooks:logbook", kwargs={"logbook_id": active.pk})

        self.assertIn(f"href='{url}'", link)
        self.assertIn(f"/logbooks/{active.pk}/", link)

    def test_hidden_or_deleted_logbook_is_not_linked(self):
        DGACAvionLogBook(ownr=self.user, name="Hidden", cat="plane_dgac", visbl=False).save()
        DGACPlaneurLogBook(ownr=self.user, name="Deleted", cat="glider_dgac", deleted=True).save()

        self.assertEqual(self.column.logbooks_link(self.profile), "Aucun logbook actif")


def test_avatar_path_accepts_filefield_upload_to_signature():
    name = UserProfile._meta.get_field("avatar").generate_filename(None, "Avatar Photo.JPG")
    assert name.startswith("avatars/")
    assert name.endswith("avatar_photo.JPG")
    assert _avatar_path(None, "avatar.jpg").endswith("avatar.jpg")

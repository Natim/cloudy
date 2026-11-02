from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Permission, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cloudy.accounts.admin import UserProfileAdmin
from cloudy.accounts.impersonation import IMPERSONATOR_SESSION_KEY
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


class ImpersonationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("root", "root@example.com", "secret")
        self.pilot = User.objects.create_user("pilot", "pilot@example.com", "secret", first_name="Ada")
        self.pilot.last_login = timezone.now() - timedelta(days=30)
        self.pilot.save(update_fields=["last_login"])
        self.profile = UserProfile.objects.create(user=self.pilot, dob="1990-01-01")
        self.client = Client()
        self.client.login(username="root", password="secret")

    def test_superuser_sees_the_site_as_the_user_and_can_return(self):
        previous_login = self.pilot.last_login
        response = self.client.post(reverse("impersonate", args=[self.pilot.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("logbooks:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.pilot.pk)
        self.assertEqual(self.client.session[IMPERSONATOR_SESSION_KEY], self.admin.pk)
        self.pilot.refresh_from_db()
        self.assertEqual(self.pilot.last_login, previous_login)

        banner = self.client.get(reverse("profile"))
        self.assertContains(banner, "vous voyez le site en tant que")
        self.assertContains(banner, "Ada")
        self.assertContains(banner, reverse("stop_impersonate"))

        self.admin.refresh_from_db()
        admin_login = self.admin.last_login
        back = self.client.post(reverse("stop_impersonate"))
        self.assertRedirects(back, reverse("admin:accounts_userprofile_change", args=[self.profile.pk]))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin.pk)
        self.assertNotIn(IMPERSONATOR_SESSION_KEY, self.client.session)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.last_login, admin_login)

    def test_change_page_offers_impersonation_to_superusers_only(self):
        url = reverse("admin:accounts_userprofile_change", args=[self.profile.pk])
        page = self.client.get(url)
        self.assertContains(page, reverse("impersonate", args=[self.pilot.pk]))
        self.assertContains(page, "Voir le site en tant que cet utilisateur")

        self.client.logout()
        staff = User.objects.create_user("staff", "staff@example.com", "secret")
        staff.is_staff = True
        staff.save()
        staff.user_permissions.add(Permission.objects.get(codename="view_userprofile"))
        self.client.login(username="staff", password="secret")
        page = self.client.get(url)
        self.assertNotContains(page, reverse("impersonate", args=[self.pilot.pk]))
        denied = self.client.post(reverse("impersonate", args=[self.pilot.pk]))
        self.assertEqual(denied.status_code, 403)

    def test_cannot_impersonate_a_superuser(self):
        other = User.objects.create_superuser("other", "other@example.com", "secret")
        UserProfile.objects.create(user=other, dob="1990-01-01")
        response = self.client.post(reverse("impersonate", args=[other.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.admin.pk)


def test_avatar_path_accepts_filefield_upload_to_signature():
    name = UserProfile._meta.get_field("avatar").generate_filename(None, "Avatar Photo.JPG")
    assert name.startswith("avatars/")
    assert name.endswith("avatar_photo.JPG")
    assert _avatar_path(None, "avatar.jpg").endswith("avatar.jpg")

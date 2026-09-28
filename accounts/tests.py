import re

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User


class AccountFlowTests(TestCase):
    def test_signup_creates_member_and_profile_even_if_role_is_submitted(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmember",
                "email": "newmember@example.test",
                "password1": "Sufficient-Password-42!",
                "password2": "Sufficient-Password-42!",
                "role": User.Role.CAMPAIGN_MANAGER,
            },
        )

        user = User.objects.get(username="newmember")
        self.assertRedirects(response, reverse("feed"))
        self.assertEqual(user.role, User.Role.MEMBER)
        self.assertEqual(user.profile.display_name, user.username)

    def test_login_logout_and_profile_edit(self):
        user = User.objects.create_user(
            username="member", password="Sufficient-Password-42!"
        )

        response = self.client.post(
            reverse("login"),
            {"username": "member", "password": "Sufficient-Password-42!"},
        )
        self.assertRedirects(response, reverse("feed"))

        response = self.client.post(
            reverse("profile-edit"),
            {"display_name": "New Name", "biography": "A short profile."},
        )
        self.assertRedirects(
            response, reverse("profile-detail", args=("member",))
        )
        user.refresh_from_db()
        self.assertEqual(user.profile.display_name, "New Name")
        self.assertEqual(user.role, User.Role.MEMBER)

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))

    def test_profile_edit_requires_authentication(self):
        response = self.client.get(reverse("profile-edit"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('profile-edit')}",
        )

    def test_login_signup_navigation_and_forms_preserve_code_range_prefix(self):
        host = settings.CODE_RANGE_HOST
        login_page = self.client.get("/accounts/login/", HTTP_HOST=host)
        self.assertContains(login_page, 'href="/proxy/5001/accounts/signup/"')
        self.assertContains(login_page, 'action="/proxy/5001/accounts/login/"')
        self.assertContains(login_page, 'href="/proxy/5001/static/css/site.css"')
        self.assertNotContains(login_page, "/proxy/5001/proxy/5001/")

        signup_page = self.client.get(
            "/proxy/5001/accounts/signup/", HTTP_HOST=host
        )
        self.assertContains(signup_page, 'href="/proxy/5001/accounts/login/"')
        self.assertContains(signup_page, 'action="/proxy/5001/accounts/signup/"')
        self.assertNotContains(signup_page, "/proxy/5001/proxy/5001/")

        signup_response = self.client.post(
            "/proxy/5001/accounts/signup/",
            {
                "username": "proxyuser",
                "email": "proxyuser@example.test",
                "password1": "Sufficient-Password-42!",
                "password2": "Sufficient-Password-42!",
            },
            HTTP_HOST=host,
        )
        self.assertRedirects(
            signup_response,
            "/proxy/5001/",
            fetch_redirect_response=False,
        )

        self.client.post("/proxy/5001/accounts/logout/", HTTP_HOST=host)
        login_response = self.client.post(
            "/proxy/5001/accounts/login/",
            {
                "username": "proxyuser",
                "password": "Sufficient-Password-42!",
            },
            HTTP_HOST=host,
        )
        self.assertRedirects(
            login_response,
            "/proxy/5001/",
            fetch_redirect_response=False,
        )

        prefixed_script = self.client.get(
            "/accounts/login/",
            HTTP_HOST=host,
            SCRIPT_NAME="/proxy/5001",
        )
        self.assertContains(prefixed_script, 'href="/proxy/5001/accounts/signup/"')
        self.assertNotContains(prefixed_script, "/proxy/5001/proxy/5001/")

        duplicated_incoming_prefix = self.client.get(
            "/proxy/5001/accounts/login/",
            HTTP_HOST=host,
            SCRIPT_NAME="/proxy/5001",
        )
        self.assertContains(
            duplicated_incoming_prefix,
            'href="/proxy/5001/accounts/signup/"',
        )
        self.assertNotContains(
            duplicated_incoming_prefix,
            "/proxy/5001/proxy/5001/",
        )

    def test_code_range_origin_allows_csrf_protected_signup_logout_and_login(self):
        origin = settings.CODE_RANGE_ORIGIN
        self.assertIn(origin, settings.CSRF_TRUSTED_ORIGINS)
        self.assertNotIn("*", settings.CSRF_TRUSTED_ORIGINS)
        client = Client(enforce_csrf_checks=True)
        host = settings.CODE_RANGE_HOST

        signup_page = client.get(
            "/proxy/5001/accounts/signup/",
            HTTP_HOST=host,
        )
        self.assertEqual(signup_page.status_code, 200)
        csrf_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            signup_page.content.decode(),
        ).group(1)
        response = client.post(
            "/proxy/5001/accounts/signup/",
            {
                "username": "trustedorigin",
                "email": "trustedorigin@example.test",
                "password1": "Sufficient-Password-42!",
                "password2": "Sufficient-Password-42!",
                "csrfmiddlewaretoken": csrf_token,
            },
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
            HTTP_REFERER=f"{origin}/proxy/5001/accounts/signup/",
        )
        self.assertRedirects(
            response,
            "/proxy/5001/",
            fetch_redirect_response=False,
        )
        self.assertTrue(User.objects.filter(username="trustedorigin").exists())

        feed = client.get("/proxy/5001/", HTTP_HOST=host)
        logout_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            feed.content.decode(),
        ).group(1)
        logout = client.post(
            "/proxy/5001/accounts/logout/",
            {"csrfmiddlewaretoken": logout_token},
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
            HTTP_REFERER=f"{origin}/proxy/5001/",
        )
        self.assertRedirects(
            logout,
            "/proxy/5001/accounts/login/",
            fetch_redirect_response=False,
        )

        login_page = client.get("/proxy/5001/accounts/login/", HTTP_HOST=host)
        login_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            login_page.content.decode(),
        ).group(1)
        login = client.post(
            "/proxy/5001/accounts/login/",
            {
                "username": "trustedorigin",
                "password": "Sufficient-Password-42!",
                "csrfmiddlewaretoken": login_token,
            },
            HTTP_HOST=host,
            HTTP_ORIGIN=origin,
            HTTP_REFERER=f"{origin}/proxy/5001/accounts/login/",
        )
        self.assertRedirects(
            login,
            "/proxy/5001/",
            fetch_redirect_response=False,
        )

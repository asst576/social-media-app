from django.test import TestCase
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

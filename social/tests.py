from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from config.testutils import make_image_upload
from social.forms import PostForm
from social.models import Follow, Post


class SocialFlowTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_settings.enable()
        self.user = User.objects.create_user(username="alice", password="safe-password")
        self.followed = User.objects.create_user(username="bob", password="safe-password")
        self.outsider = User.objects.create_user(username="cara", password="safe-password")
        self.client.force_login(self.user)

    def tearDown(self):
        self.media_settings.disable()
        self.media_directory.cleanup()
        super().tearDown()

    def test_post_accepts_text_image_or_both_and_rejects_empty(self):
        response = self.client.post(reverse("post-create"), {"body": "A text post"})
        self.assertRedirects(response, reverse("feed"))

        response = self.client.post(
            reverse("post-create"), {"body": "", "image": make_image_upload()}
        )
        self.assertRedirects(response, reverse("feed"))

        response = self.client.post(
            reverse("post-create"),
            {"body": "Both", "image": make_image_upload("both.png")},
        )
        self.assertRedirects(response, reverse("feed"))
        self.assertEqual(Post.objects.filter(author=self.user).count(), 3)

        response = self.client.post(reverse("post-create"), {"body": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.filter(author=self.user).count(), 3)

    def test_post_rejects_malformed_and_oversized_images(self):
        malformed = SimpleUploadedFile("fake.png", b"not an image", "image/png")
        response = self.client.post(
            reverse("post-create"), {"body": "", "image": malformed}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

        oversized = SimpleUploadedFile(
            "large.png", b"x" * (5 * 1024 * 1024 + 1), "image/png"
        )
        form = PostForm(data={"body": ""}, files={"image": oversized})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

        with override_settings(MAX_IMAGE_PIXELS=32):
            form = PostForm(
                data={"body": "Image dimensions"},
                files={"image": make_image_upload("dimensions.png")},
            )
            self.assertFalse(form.is_valid())
            self.assertIn("image", form.errors)

    def test_follow_unfollow_is_directional_and_idempotent(self):
        response = self.client.post(
            reverse("follow", args=(self.followed.username,))
        )
        self.assertRedirects(
            response, reverse("profile-detail", args=(self.followed.username,))
        )
        self.client.post(reverse("follow", args=(self.followed.username,)))
        self.assertEqual(Follow.objects.filter(follower=self.user).count(), 1)
        self.assertFalse(
            Follow.objects.filter(follower=self.followed, followed=self.user).exists()
        )

        response = self.client.get(reverse("follow", args=(self.outsider.username,)))
        self.assertRedirects(
            response, reverse("profile-detail", args=(self.outsider.username,))
        )
        self.assertFalse(
            Follow.objects.filter(follower=self.user, followed=self.outsider).exists()
        )

        self.client.post(reverse("follow", args=(self.user.username,)))
        self.assertFalse(
            Follow.objects.filter(follower=self.user, followed=self.user).exists()
        )

        response = self.client.post(
            reverse("unfollow", args=(self.followed.username,))
        )
        self.assertRedirects(
            response, reverse("profile-detail", args=(self.followed.username,))
        )
        self.assertFalse(Follow.objects.filter(follower=self.user).exists())

    def test_database_rejects_duplicate_and_self_follow_rows(self):
        Follow.objects.create(follower=self.user, followed=self.followed)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.user, followed=self.followed)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Follow.objects.create(follower=self.user, followed=self.user)

    def test_feed_contains_own_and_followed_posts_but_not_unrelated_posts(self):
        own = Post.objects.create(author=self.user, body="My post")
        followed_post = Post.objects.create(author=self.followed, body="Followed post")
        Post.objects.create(author=self.outsider, body="Outsider post")
        Follow.objects.create(follower=self.user, followed=self.followed)

        response = self.client.get(reverse("feed"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My post")
        self.assertContains(response, "Followed post")
        self.assertNotContains(response, "Outsider post")
        self.assertEqual(
            [item["post"].pk for item in response.context["feed_items"]],
            [followed_post.pk, own.pk],
        )

        self.client.post(reverse("unfollow", args=(self.followed.username,)))
        response = self.client.get(reverse("feed"))
        self.assertNotContains(response, "Followed post")

    def test_feed_is_paginated(self):
        for number in range(12):
            Post.objects.create(author=self.user, body=f"Post {number}")

        response = self.client.get(reverse("feed"))

        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertTrue(response.context["page_obj"].has_next())

    def test_repost_references_original_and_is_idempotent(self):
        original = Post.objects.create(author=self.followed, body="Original text")

        response = self.client.post(reverse("repost", args=(original.pk,)))
        self.assertRedirects(response, reverse("feed"))
        self.client.post(reverse("repost", args=(original.pk,)))

        reposted = Post.objects.get(author=self.user, repost_of=original)
        self.assertEqual(reposted.body, "")
        self.assertFalse(reposted.image)
        self.assertEqual(Post.objects.filter(author=self.user, repost_of=original).count(), 1)
        self.assertContains(self.client.get(reverse("feed")), "Original text")

    def test_reposting_own_post_or_another_repost_is_not_allowed(self):
        own = Post.objects.create(author=self.user, body="Own post")
        original = Post.objects.create(author=self.followed, body="Original")
        shared = Post.objects.create(author=self.outsider, repost_of=original)

        self.client.post(reverse("repost", args=(own.pk,)))
        response = self.client.post(reverse("repost", args=(shared.pk,)))

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Post.objects.filter(author=self.user, repost_of=own).exists())
        self.assertFalse(Post.objects.filter(author=self.user, repost_of=shared).exists())

    def test_profile_shows_follow_controls_and_user_posts(self):
        Post.objects.create(author=self.followed, body="On the profile")
        response = self.client.get(
            reverse("profile-detail", args=(self.followed.username,))
        )
        self.assertContains(response, "On the profile")
        self.assertContains(response, "Follow")

    def test_people_directory_lists_others_and_their_follow_state(self):
        response = self.client.get(reverse("people"))
        listed_ids = {person.pk for person in response.context["page_obj"]}
        self.assertEqual(listed_ids, {self.followed.pk, self.outsider.pk})
        self.assertNotIn(self.user.pk, listed_ids)

        self.client.post(reverse("follow", args=(self.followed.username,)))
        response = self.client.get(reverse("people"))
        followed = next(
            person
            for person in response.context["page_obj"]
            if person.pk == self.followed.pk
        )
        self.assertTrue(followed.is_following)

    def test_mutations_require_post_and_csrf(self):
        protected_client = Client(enforce_csrf_checks=True)
        protected_client.force_login(self.user)

        response = protected_client.post(
            reverse("follow", args=(self.followed.username,))
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Follow.objects.filter(follower=self.user, followed=self.followed).exists()
        )

    def test_repost_does_not_redirect_to_an_external_referer(self):
        original = Post.objects.create(author=self.followed, body="Original")

        response = self.client.post(
            reverse("repost", args=(original.pk,)),
            HTTP_REFERER="https://example.invalid/",
        )

        self.assertRedirects(response, reverse("feed"))

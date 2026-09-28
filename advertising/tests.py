from datetime import timedelta
from tempfile import TemporaryDirectory

from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from advertising.forms import CampaignForm
from advertising.models import Campaign
from advertising.services import eligible_campaigns
from config.testutils import make_image_upload
from social.models import Post


class CampaignFlowTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_settings.enable()
        self.manager = User.objects.create_user(
            username="manager",
            password="safe-password",
            role=User.Role.CAMPAIGN_MANAGER,
        )
        self.member = User.objects.create_user(username="member", password="safe-password")
        self.staff = User.objects.create_superuser(
            username="staff", email="staff@example.test", password="safe-password"
        )

    def tearDown(self):
        self.media_settings.disable()
        self.media_directory.cleanup()
        super().tearDown()

    def campaign_data(self, **overrides):
        now = timezone.now().replace(second=0, microsecond=0)
        data = {
            "name": "Spring campaign",
            "headline": "Read something new",
            "body": "A small sponsored message.",
            "budget": "12.50",
            "starts_at": (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
            "ends_at": (now + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M"),
        }
        data.update(overrides)
        return data

    def create_campaign(self, **overrides):
        now = timezone.now()
        values = {
            "owner": self.manager,
            "name": "Campaign",
            "headline": "Headline",
            "body": "Sponsored message",
            "budget_cents": 1250,
            "currency": "USD",
            "starts_at": now - timedelta(hours=1),
            "ends_at": now + timedelta(days=1),
        }
        values.update(overrides)
        return Campaign.objects.create(**values)

    def test_campaign_manager_can_create_text_and_image_draft(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("campaign-create"),
            {**self.campaign_data(), "image": make_image_upload("campaign.png")},
        )

        campaign = Campaign.objects.get(owner=self.manager)
        self.assertRedirects(
            response, reverse("campaign-detail", args=(campaign.pk,))
        )
        self.assertEqual(campaign.status, Campaign.Status.DRAFT)
        self.assertEqual(campaign.budget_cents, 1250)
        self.assertEqual(campaign.currency, "USD")
        self.assertTrue(campaign.image)

    def test_regular_member_cannot_manage_campaigns(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("campaign-create"))
        self.assertEqual(response.status_code, 403)

    def test_campaign_ownership_is_enforced(self):
        campaign = self.create_campaign()
        other_manager = User.objects.create_user(
            username="other-manager",
            password="safe-password",
            role=User.Role.CAMPAIGN_MANAGER,
        )
        self.client.force_login(other_manager)

        response = self.client.get(reverse("campaign-detail", args=(campaign.pk,)))
        self.assertEqual(response.status_code, 404)

    def test_manager_submits_campaign_staff_approves_then_purchase_is_simulated(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("campaign-create"), self.campaign_data())
        campaign = Campaign.objects.get(owner=self.manager)
        self.assertRedirects(response, reverse("campaign-detail", args=(campaign.pk,)))

        response = self.client.post(reverse("campaign-submit", args=(campaign.pk,)))
        self.assertRedirects(response, reverse("campaign-detail", args=(campaign.pk,)))
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.PENDING_REVIEW)
        self.assertFalse(campaign.simulated_paid)

        self.client.post(reverse("campaign-purchase", args=(campaign.pk,)))
        campaign.refresh_from_db()
        self.assertFalse(campaign.simulated_paid)

        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("admin:advertising_campaign_changelist"),
            {
                "action": "approve_campaigns",
                "_selected_action": [campaign.pk],
                "index": "0",
            },
        )
        self.assertEqual(response.status_code, 302)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.APPROVED)
        self.assertEqual(campaign.reviewed_by, self.staff)
        self.assertFalse(campaign.simulated_paid)

        self.client.force_login(self.manager)
        response = self.client.post(reverse("campaign-purchase", args=(campaign.pk,)))
        self.assertRedirects(response, reverse("campaign-detail", args=(campaign.pk,)))
        campaign.refresh_from_db()
        self.assertTrue(campaign.simulated_paid)
        self.assertIsNotNone(campaign.paid_at)
        self.assertTrue(campaign.is_eligible())
        self.assertContains(
            self.client.get(reverse("campaign-detail", args=(campaign.pk,))),
            "no money transferred",
        )

        paid_at = campaign.paid_at
        self.client.post(reverse("campaign-purchase", args=(campaign.pk,)))
        campaign.refresh_from_db()
        self.assertEqual(campaign.paid_at, paid_at)

    def test_campaign_form_has_no_payment_or_moderation_fields(self):
        form = CampaignForm()
        self.assertNotIn("simulated_paid", form.fields)
        self.assertNotIn("status", form.fields)
        self.assertNotIn("card_number", form.fields)
        self.assertNotIn("payment_method", form.fields)

    def test_campaign_submission_requires_csrf(self):
        campaign = self.create_campaign()
        protected_client = Client(enforce_csrf_checks=True)
        protected_client.force_login(self.manager)

        response = protected_client.post(reverse("campaign-submit", args=(campaign.pk,)))

        self.assertEqual(response.status_code, 403)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.DRAFT)

    def test_expired_campaign_cannot_be_purchased(self):
        campaign = self.create_campaign(
            status=Campaign.Status.APPROVED,
            ends_at=timezone.now() - timedelta(minutes=1),
        )
        self.client.force_login(self.manager)

        self.client.post(reverse("campaign-purchase", args=(campaign.pk,)))

        campaign.refresh_from_db()
        self.assertFalse(campaign.simulated_paid)
        self.assertIsNone(campaign.paid_at)

    def test_invalid_budget_or_date_range_is_rejected(self):
        invalid_budget = CampaignForm(
            data=self.campaign_data(budget="0.00")
        )
        self.assertFalse(invalid_budget.is_valid())
        self.assertIn("budget", invalid_budget.errors)

        invalid_dates = CampaignForm(
            data=self.campaign_data(
                starts_at="2026-01-02T12:00",
                ends_at="2026-01-01T12:00",
            )
        )
        self.assertFalse(invalid_dates.is_valid())

    def test_database_rejects_nonpositive_budget_and_inverted_dates(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_campaign(name="Zero budget", budget_cents=0)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_campaign(
                    name="Inverted dates",
                    starts_at=timezone.now(),
                    ends_at=timezone.now() - timedelta(days=1),
                )

    def test_eligibility_requires_approval_purchase_and_current_schedule(self):
        eligible = self.create_campaign(
            status=Campaign.Status.APPROVED,
            simulated_paid=True,
        )
        unpaid = self.create_campaign(
            name="Unpaid",
            status=Campaign.Status.APPROVED,
            simulated_paid=False,
        )
        pending = self.create_campaign(
            name="Pending",
            status=Campaign.Status.PENDING_REVIEW,
            simulated_paid=True,
        )
        future = self.create_campaign(
            name="Future",
            status=Campaign.Status.APPROVED,
            simulated_paid=True,
            starts_at=timezone.now() + timedelta(days=1),
        )
        expired = self.create_campaign(
            name="Expired",
            status=Campaign.Status.APPROVED,
            simulated_paid=True,
            starts_at=timezone.now() - timedelta(days=2),
            ends_at=timezone.now() - timedelta(days=1),
        )

        ids = set(eligible_campaigns().values_list("pk", flat=True))
        self.assertEqual(ids, {eligible.pk})
        self.assertTrue(eligible.is_eligible(eligible.starts_at))
        self.assertFalse(eligible.is_eligible(eligible.ends_at))
        self.assertFalse(unpaid.is_eligible())
        self.assertFalse(pending.is_eligible())
        self.assertFalse(future.is_eligible())
        self.assertFalse(expired.is_eligible())

    def test_sponsored_content_is_separate_and_inserted_after_five_organic_items(self):
        campaign = self.create_campaign(
            status=Campaign.Status.APPROVED,
            simulated_paid=True,
        )
        for number in range(6):
            Post.objects.create(author=self.member, body=f"Organic {number}")

        self.client.force_login(self.member)
        response = self.client.get(reverse("feed"))

        self.assertEqual(response.status_code, 200)
        feed_items = response.context["feed_items"]
        self.assertEqual(feed_items[5]["kind"], "ad")
        self.assertEqual(feed_items[5]["campaign"], campaign)
        self.assertEqual(Post.objects.count(), 6)
        self.assertContains(response, "Sponsored")
        self.assertContains(response, campaign.headline)

    def test_ineligible_campaigns_do_not_appear_in_feed(self):
        campaign = self.create_campaign(
            status=Campaign.Status.PENDING_REVIEW,
            simulated_paid=True,
        )
        for number in range(5):
            Post.objects.create(author=self.member, body=f"Organic {number}")
        self.client.force_login(self.member)

        response = self.client.get(reverse("feed"))

        self.assertNotContains(response, "Sponsored")
        self.assertNotContains(response, campaign.headline)

    def test_sponsored_campaigns_rotate_between_feed_requests(self):
        first = self.create_campaign(
            name="First", status=Campaign.Status.APPROVED, simulated_paid=True
        )
        second = self.create_campaign(
            name="Second", status=Campaign.Status.APPROVED, simulated_paid=True
        )
        for number in range(5):
            Post.objects.create(author=self.member, body=f"Organic {number}")
        self.client.force_login(self.member)

        first_response = self.client.get(reverse("feed"))
        second_response = self.client.get(reverse("feed"))

        self.assertEqual(first_response.context["feed_items"][5]["campaign"], first)
        self.assertEqual(second_response.context["feed_items"][5]["campaign"], second)

    def test_staff_can_pause_and_resume_approved_campaigns(self):
        campaign = self.create_campaign(
            status=Campaign.Status.APPROVED,
            simulated_paid=True,
        )
        self.client.force_login(self.staff)
        changelist = reverse("admin:advertising_campaign_changelist")

        self.client.post(
            changelist,
            {
                "action": "pause_campaigns",
                "_selected_action": [campaign.pk],
                "index": "0",
            },
        )
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.PAUSED)
        self.assertFalse(campaign.is_eligible())

        self.client.post(
            changelist,
            {
                "action": "resume_campaigns",
                "_selected_action": [campaign.pk],
                "index": "0",
            },
        )
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.APPROVED)
        self.assertTrue(campaign.is_eligible())

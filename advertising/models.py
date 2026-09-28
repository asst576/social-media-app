from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from config.validators import campaign_image_upload_path, validate_image_upload


class Campaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_REVIEW = "pending_review", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PAUSED = "paused", "Paused"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    name = models.CharField(max_length=100)
    headline = models.CharField(max_length=120)
    body = models.TextField(max_length=500)
    image = models.ImageField(
        upload_to=campaign_image_upload_path,
        blank=True,
        validators=(validate_image_upload,),
    )
    budget_cents = models.PositiveBigIntegerField(validators=(MinValueValidator(1),))
    currency = models.CharField(max_length=3, default="USD")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    simulated_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_campaigns",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=Q(budget_cents__gt=0), name="campaign_budget_positive"
            ),
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")),
                name="campaign_end_after_start",
            ),
        ]

    def clean(self):
        errors = {}
        if self.owner_id and self.owner.role != self.owner.Role.CAMPAIGN_MANAGER:
            errors["owner"] = "Campaigns must be owned by a campaign manager."
        if self.budget_cents is not None and self.budget_cents < 1:
            errors["budget_cents"] = "Campaign budget must be greater than zero."
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            errors["ends_at"] = "Campaign end must be later than its start."
        if errors:
            raise ValidationError(errors)

    def is_eligible(self, at=None):
        at = at or timezone.now()
        return (
            self.status == self.Status.APPROVED
            and self.simulated_paid
            and self.starts_at <= at < self.ends_at
        )

    @property
    def formatted_budget(self):
        amount = Decimal(self.budget_cents) / Decimal(100)
        return f"{self.currency} {amount:,.2f}"

    def __str__(self):
        return self.name

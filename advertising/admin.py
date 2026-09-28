from django.contrib import admin, messages
from django.utils import timezone

from advertising.models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "status",
        "simulated_paid",
        "starts_at",
        "ends_at",
    )
    list_filter = ("status", "simulated_paid")
    search_fields = ("name", "owner__username", "headline", "body")
    readonly_fields = (
        "status",
        "simulated_paid",
        "paid_at",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    actions = (
        "approve_campaigns",
        "reject_campaigns",
        "pause_campaigns",
        "resume_campaigns",
    )

    @admin.action(description="Approve selected pending campaigns")
    def approve_campaigns(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(status=Campaign.Status.PENDING_REVIEW).update(
            status=Campaign.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=now,
        )
        self.message_user(request, f"Approved {updated} campaign(s).", messages.SUCCESS)

    @admin.action(description="Reject selected pending campaigns")
    def reject_campaigns(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(status=Campaign.Status.PENDING_REVIEW).update(
            status=Campaign.Status.REJECTED,
            reviewed_by=request.user,
            reviewed_at=now,
        )
        self.message_user(request, f"Rejected {updated} campaign(s).", messages.SUCCESS)

    @admin.action(description="Pause selected approved campaigns")
    def pause_campaigns(self, request, queryset):
        updated = queryset.filter(status=Campaign.Status.APPROVED).update(
            status=Campaign.Status.PAUSED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"Paused {updated} campaign(s).", messages.SUCCESS)

    @admin.action(description="Resume selected paused campaigns")
    def resume_campaigns(self, request, queryset):
        updated = queryset.filter(status=Campaign.Status.PAUSED).update(
            status=Campaign.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"Resumed {updated} campaign(s).", messages.SUCCESS)

from django.utils import timezone

from advertising.models import Campaign


def eligible_campaigns(at=None):
    at = at or timezone.now()
    return (
        Campaign.objects.filter(
            status=Campaign.Status.APPROVED,
            simulated_paid=True,
            starts_at__lte=at,
            ends_at__gt=at,
        )
        .select_related("owner", "owner__profile")
        .order_by("pk")
    )

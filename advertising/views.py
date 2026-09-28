from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from advertising.forms import CampaignForm
from advertising.models import Campaign


def campaign_manager_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.role != User.Role.CAMPAIGN_MANAGER:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


@campaign_manager_required
def campaign_list(request):
    campaigns = Campaign.objects.filter(owner=request.user)
    return render(request, "advertising/campaign_list.html", {"campaigns": campaigns})


@campaign_manager_required
def campaign_create(request):
    form = CampaignForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.owner = request.user
        campaign.status = Campaign.Status.DRAFT
        campaign.full_clean()
        campaign.save()
        messages.success(request, "Campaign saved as a draft.")
        return redirect("campaign-detail", pk=campaign.pk)
    return render(request, "advertising/campaign_form.html", {"form": form})


@campaign_manager_required
def campaign_edit(request, pk):
    campaign = get_object_or_404(
        Campaign.objects.filter(owner=request.user),
        pk=pk,
        status__in=(Campaign.Status.DRAFT, Campaign.Status.REJECTED),
    )
    form = CampaignForm(request.POST or None, request.FILES or None, instance=campaign)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.owner = request.user
        campaign.full_clean()
        campaign.save()
        messages.success(request, "Campaign updated.")
        return redirect("campaign-detail", pk=campaign.pk)
    return render(
        request,
        "advertising/campaign_form.html",
        {"form": form, "campaign": campaign},
    )


@campaign_manager_required
def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk, owner=request.user)
    return render(
        request,
        "advertising/campaign_detail.html",
        {
            "campaign": campaign,
            "is_active": campaign.is_eligible(),
            "currency": settings.DEFAULT_CURRENCY,
        },
    )


@campaign_manager_required
def campaign_submit(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    campaign = get_object_or_404(
        Campaign.objects.filter(owner=request.user),
        pk=pk,
        status__in=(Campaign.Status.DRAFT, Campaign.Status.REJECTED),
    )
    campaign.full_clean()
    campaign.status = Campaign.Status.PENDING_REVIEW
    campaign.reviewed_by = None
    campaign.reviewed_at = None
    campaign.simulated_paid = False
    campaign.paid_at = None
    campaign.save()
    messages.success(request, "Campaign submitted for staff review.")
    return redirect("campaign-detail", pk=campaign.pk)


@campaign_manager_required
@transaction.atomic
def campaign_purchase(request, pk):
    if request.method != "POST":
        raise PermissionDenied
    campaign = get_object_or_404(
        Campaign.objects.select_for_update(), pk=pk, owner=request.user
    )
    if campaign.status != Campaign.Status.APPROVED:
        messages.error(request, "A campaign must be approved before the demo purchase.")
        return redirect("campaign-detail", pk=campaign.pk)
    if campaign.ends_at <= timezone.now():
        messages.error(request, "An expired campaign cannot be purchased.")
        return redirect("campaign-detail", pk=campaign.pk)
    if not campaign.simulated_paid:
        campaign.simulated_paid = True
        campaign.paid_at = timezone.now()
        campaign.save(update_fields=("simulated_paid", "paid_at"))
        messages.success(
            request,
            "Demo purchase recorded. No money was transferred.",
        )
    else:
        messages.info(request, "This campaign has already been purchased in the demo.")
    return redirect("campaign-detail", pk=campaign.pk)

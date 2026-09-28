from decimal import Decimal

from django import forms
from django.conf import settings

from advertising.models import Campaign


class CampaignForm(forms.ModelForm):
    budget = forms.DecimalField(
        max_digits=9,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Demo campaign amount. No payment is taken.",
    )

    class Meta:
        model = Campaign
        fields = ("name", "headline", "body", "image", "starts_at", "ends_at")
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
            "starts_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }
        input_formats = ["%Y-%m-%dT%H:%M"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["budget"].initial = (
            Decimal(self.instance.budget_cents) / 100
            if self.instance.pk
            else Decimal("10.00")
        )
        self.fields["budget"].label = f"Budget ({settings.DEFAULT_CURRENCY})"

    def clean(self):
        cleaned_data = super().clean()
        budget = cleaned_data.get("budget")
        if budget is not None:
            self.instance.budget_cents = int(budget * 100)
            self.instance.currency = settings.DEFAULT_CURRENCY
        return cleaned_data

    def save(self, commit=True):
        campaign = super().save(commit=False)
        campaign.budget_cents = int(self.cleaned_data["budget"] * 100)
        campaign.currency = settings.DEFAULT_CURRENCY
        if commit:
            campaign.save()
            self.save_m2m()
        return campaign

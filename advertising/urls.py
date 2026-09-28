from django.urls import path

from advertising.views import (
    campaign_create,
    campaign_detail,
    campaign_edit,
    campaign_list,
    campaign_purchase,
    campaign_submit,
)

urlpatterns = [
    path("", campaign_list, name="campaign-list"),
    path("new/", campaign_create, name="campaign-create"),
    path("<int:pk>/", campaign_detail, name="campaign-detail"),
    path("<int:pk>/edit/", campaign_edit, name="campaign-edit"),
    path("<int:pk>/submit/", campaign_submit, name="campaign-submit"),
    path("<int:pk>/purchase/", campaign_purchase, name="campaign-purchase"),
]

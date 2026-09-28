from django.contrib.auth.views import LogoutView
from django.urls import path

from accounts.views import UserLoginView, profile_detail, profile_edit, signup

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/edit/", profile_edit, name="profile-edit"),
    path("users/<str:username>/", profile_detail, name="profile-detail"),
]

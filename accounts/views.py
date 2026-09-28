from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import ProfileForm, SignUpForm
from accounts.models import Profile, User


class UserLoginView(LoginView):
    template_name = "registration/login.html"


def signup(request):
    if request.user.is_authenticated:
        return redirect("feed")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("feed")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def profile_detail(request, username):
    from social.models import Follow

    profile_user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(
        user=profile_user,
        defaults={"display_name": profile_user.username},
    )
    is_following = (
        request.user.is_authenticated
        and Follow.objects.filter(follower=request.user, followed=profile_user).exists()
    )
    return render(
        request,
        "accounts/profile_detail.html",
        {
            "profile_user": profile_user,
            "profile": profile,
            "posts": profile_user.posts.select_related(
                "author", "author__profile", "repost_of", "repost_of__author"
            ).order_by("-created_at", "-pk"),
            "is_following": is_following,
            "follower_count": profile_user.followers.count(),
            "following_count": profile_user.following.count(),
        },
    )


@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.username},
    )
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile-detail", username=request.user.username)
    return render(request, "accounts/profile_edit.html", {"form": form})

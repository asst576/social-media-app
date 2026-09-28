from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.models import User
from social.forms import PostForm
from social.models import Follow, Post


@login_required
def feed(request):
    from advertising.services import eligible_campaigns

    followed_ids = Follow.objects.filter(follower=request.user).values("followed_id")
    posts = (
        Post.objects.filter(Q(author=request.user) | Q(author_id__in=followed_ids))
        .select_related(
            "author",
            "author__profile",
            "repost_of",
            "repost_of__author",
            "repost_of__author__profile",
        )
        .order_by("-created_at", "-pk")
    )
    page_obj = Paginator(posts, 10).get_page(request.GET.get("page"))
    campaigns = list(eligible_campaigns())
    rotation_start = request.session.get("ad_rotation", 0) % len(campaigns) if campaigns else 0

    feed_items = []
    ad_index = 0
    for organic_index, post in enumerate(page_obj.object_list, start=1):
        feed_items.append({"kind": "post", "post": post})
        if organic_index % 5 == 0 and campaigns:
            feed_items.append(
                {
                    "kind": "ad",
                    "campaign": campaigns[(rotation_start + ad_index) % len(campaigns)],
                }
            )
            ad_index += 1
    if ad_index:
        request.session["ad_rotation"] = (rotation_start + ad_index) % len(campaigns)

    return render(
        request,
        "social/feed.html",
        {"page_obj": page_obj, "feed_items": feed_items},
    )


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Post published.")
        return redirect("feed")
    return render(request, "social/post_form.html", {"form": form})


@login_required
def people(request):
    followed = Follow.objects.filter(follower=request.user, followed=OuterRef("pk"))
    users = (
        User.objects.exclude(pk=request.user.pk)
        .select_related("profile")
        .annotate(is_following=Exists(followed))
        .order_by("username")
    )
    page_obj = Paginator(users, 20).get_page(request.GET.get("page"))
    return render(request, "social/people.html", {"page_obj": page_obj})


@login_required
def follow_user(request, username):
    if request.method != "POST":
        return redirect("profile-detail", username=username)
    followed = get_object_or_404(User, username=username)
    if followed == request.user:
        messages.error(request, "You cannot follow yourself.")
    else:
        Follow.objects.get_or_create(follower=request.user, followed=followed)
    return redirect("profile-detail", username=username)


@login_required
def unfollow_user(request, username):
    if request.method != "POST":
        return redirect("profile-detail", username=username)
    followed = get_object_or_404(User, username=username)
    Follow.objects.filter(follower=request.user, followed=followed).delete()
    return redirect("profile-detail", username=username)


@login_required
def repost(request, post_id):
    if request.method != "POST":
        return redirect("feed")
    original = get_object_or_404(Post, pk=post_id, repost_of__isnull=True)
    if original.author == request.user:
        messages.error(request, "You cannot repost your own post.")
    else:
        Post.objects.get_or_create(
            author=request.user,
            repost_of=original,
            defaults={"body": ""},
        )
        messages.success(request, "Post shared to your profile.")
    referer = request.META.get("HTTP_REFERER", "")
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect("feed")

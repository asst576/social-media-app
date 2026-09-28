from django.urls import path

from social.views import create_post, feed, follow_user, people, repost, unfollow_user

urlpatterns = [
    path("", feed, name="feed"),
    path("people/", people, name="people"),
    path("posts/new/", create_post, name="post-create"),
    path("posts/<int:post_id>/repost/", repost, name="repost"),
    path("users/<str:username>/follow/", follow_user, name="follow"),
    path("users/<str:username>/unfollow/", unfollow_user, name="unfollow"),
]

from django.contrib import admin

from social.models import Follow, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "created_at", "repost_of")
    list_filter = ("created_at",)
    search_fields = ("author__username", "body")
    readonly_fields = ("created_at",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followed", "created_at")
    list_filter = ("created_at",)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Profile, User


@admin.register(User)
class ProjectUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Project role", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Project role", {"fields": ("role",)}),
    )
    list_display = UserAdmin.list_display + ("role",)
    list_filter = UserAdmin.list_filter + ("role",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user")
    search_fields = ("display_name", "user__username")

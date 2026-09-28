from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MEMBER = "member", "Regular member"
        CAMPAIGN_MANAGER = "campaign_manager", "Campaign manager"

    role = models.CharField(
        max_length=24,
        choices=Role.choices,
        default=Role.MEMBER,
    )


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=80)
    biography = models.CharField(max_length=280, blank=True)

    def __str__(self):
        return self.display_name

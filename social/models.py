from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from config.validators import post_image_upload_path, validate_image_upload


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("follower", "followed"), name="unique_follow_pair"
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("followed")), name="no_self_follow"
            ),
        ]
        indexes = [models.Index(fields=("follower", "created_at"))]

    def clean(self):
        if self.follower_id and self.follower_id == self.followed_id:
            raise ValidationError("You cannot follow yourself.")

    def __str__(self):
        return f"{self.follower} follows {self.followed}"


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    body = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=post_image_upload_path,
        blank=True,
        validators=(validate_image_upload,),
    )
    repost_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reposts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(repost_of__isnull=False, body="", image="")
                    | (
                        Q(repost_of__isnull=True)
                        & (~Q(body="") | ~Q(image=""))
                    )
                ),
                name="post_has_content_or_is_repost",
            ),
            models.UniqueConstraint(
                fields=("author", "repost_of"),
                condition=Q(repost_of__isnull=False),
                name="unique_user_repost",
            ),
        ]
        indexes = [models.Index(fields=("author", "-created_at", "-id"))]

    def clean(self):
        if self.repost_of_id:
            if self.repost_of_id == self.pk:
                raise ValidationError("A post cannot repost itself.")
            if self.repost_of.repost_of_id:
                raise ValidationError("Only original posts can be reposted.")
            if self.repost_of.author_id == self.author_id:
                raise ValidationError("You cannot repost your own post.")
            if self.body.strip() or self.image:
                raise ValidationError("A repost cannot duplicate post content.")
        elif not self.body.strip() and not self.image:
            raise ValidationError("Add text, an image, or both to your post.")

    def __str__(self):
        if self.repost_of_id:
            return f"{self.author} reposted {self.repost_of_id}"
        return f"Post by {self.author}"

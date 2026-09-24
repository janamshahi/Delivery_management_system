from django.db import models
from django.contrib.auth.models import User
from parcels.models import Parcel


class Notification(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    parcel = models.ForeignKey(
        Parcel,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ['-created_at']
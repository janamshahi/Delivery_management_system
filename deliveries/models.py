from django.db import models
from django.contrib.auth.models import User
from parcels.models import Parcel


class Delivery(models.Model):

    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed Delivery'),
        ('rescheduled', 'Rescheduled'),
    ]

    parcel = models.OneToOneField(
        Parcel,
        on_delete=models.CASCADE,
        related_name='delivery'
    )

    delivery_staff = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_deliveries'
    )

    assigned_date = models.DateTimeField(
        auto_now_add=True
    )

    pickup_time = models.DateTimeField(
        null=True,
        blank=True
    )

    delivery_time = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='assigned'
    )

    proof_of_delivery = models.ImageField(
        upload_to='proof_of_delivery/',
        null=True,
        blank=True
    )

    remarks = models.TextField(
        blank=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        staff_name = (
            self.delivery_staff.get_full_name()
            if self.delivery_staff
            else "Not Assigned"
        )

        return f"{self.parcel.tracking_number} - {staff_name}"

    class Meta:
        ordering = ['-assigned_date']
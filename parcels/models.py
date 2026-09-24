from django.db import models
from django.contrib.auth.models import User


# ============================================================
# PARCEL MODEL
# ============================================================

class Parcel(models.Model):

    # --------------------------------------------------------
    # Parcel Type Choices
    # --------------------------------------------------------

    PARCEL_TYPE_CHOICES = [
        ('document', 'Document'),
        ('package', 'Package'),
        ('fragile', 'Fragile Item'),
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('food', 'Food Item'),
        ('other', 'Other'),
    ]

    # --------------------------------------------------------
    # Parcel Status Choices
    # --------------------------------------------------------

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('pickup_requested', 'Pickup Requested'),
        ('assigned', 'Assigned'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed Delivery'),
        ('rescheduled', 'Rescheduled'),
    ]

    # --------------------------------------------------------
    # Customer Information
    # --------------------------------------------------------

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parcels'
    )

    # --------------------------------------------------------
    # Tracking Information
    # --------------------------------------------------------

    tracking_number = models.CharField(
        max_length=30,
        unique=True
    )

    # --------------------------------------------------------
    # Sender Information
    # --------------------------------------------------------

    sender_name = models.CharField(
        max_length=150
    )

    sender_phone = models.CharField(
        max_length=15
    )

    sender_address = models.TextField()

    # --------------------------------------------------------
    # Receiver Information
    # --------------------------------------------------------

    receiver_name = models.CharField(
        max_length=150
    )

    receiver_phone = models.CharField(
        max_length=15
    )

    receiver_address = models.TextField()

    # --------------------------------------------------------
    # Parcel Information
    # --------------------------------------------------------

    parcel_type = models.CharField(
        max_length=30,
        choices=PARCEL_TYPE_CHOICES,
        default='package'
    )

    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    # --------------------------------------------------------
    # Delivery Information
    # --------------------------------------------------------

    pickup_date = models.DateField(
        null=True,
        blank=True
    )

    delivery_date = models.DateField(
        null=True,
        blank=True
    )

    # --------------------------------------------------------
    # Delivery Charge
    #
    # This value will be calculated from the weight according
    # to the rates configured by the administrator.
    # --------------------------------------------------------

    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # --------------------------------------------------------
    # Current Parcel Status
    # --------------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # --------------------------------------------------------
    # Timestamps
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # --------------------------------------------------------
    # String Representation
    # --------------------------------------------------------

    def __str__(self):
        return self.tracking_number

    # --------------------------------------------------------
    # Meta
    # --------------------------------------------------------

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Parcel'
        verbose_name_plural = 'Parcels'


# ============================================================
# TRACKING HISTORY MODEL
# ============================================================

class TrackingHistory(models.Model):

    # --------------------------------------------------------
    # Related Parcel
    # --------------------------------------------------------

    parcel = models.ForeignKey(
        Parcel,
        on_delete=models.CASCADE,
        related_name='tracking_history'
    )

    # --------------------------------------------------------
    # Status at This Tracking Event
    # --------------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=Parcel.STATUS_CHOICES
    )

    # --------------------------------------------------------
    # Current Location
    # --------------------------------------------------------

    location = models.CharField(
        max_length=200,
        blank=True
    )

    # --------------------------------------------------------
    # Additional Remarks
    # --------------------------------------------------------

    remarks = models.TextField(
        blank=True
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # --------------------------------------------------------
    # String Representation
    # --------------------------------------------------------

    def __str__(self):
        return (
            f"{self.parcel.tracking_number} - "
            f"{self.get_status_display()}"
        )

    # --------------------------------------------------------
    # Meta
    # --------------------------------------------------------

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Tracking History'
        verbose_name_plural = 'Tracking Histories'


# ============================================================
# DELIVERY CHARGE RATE MODEL
# ============================================================
#
# This model stores the delivery charges configured by the
# SHATHIMART administrator.
#
# Example:
#
# Up to 1 kg       = Rs. 100
# Above 1 - 3 kg   = Rs. 150
# Above 3 - 5 kg   = Rs. 200
# Above 5 kg       = Rs. 300
#
# The administrator can change these values from the
# Delivery Charges page in the admin dashboard.
#
# The Create Parcel page will then use these saved values
# automatically.
# ============================================================

class DeliveryChargeRate(models.Model):

    # --------------------------------------------------------
    # Charge for parcels weighing up to 1 kg
    # --------------------------------------------------------

    up_to_1kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00
    )

    # --------------------------------------------------------
    # Charge for parcels above 1 kg and up to 3 kg
    # --------------------------------------------------------

    up_to_3kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=150.00
    )

    # --------------------------------------------------------
    # Charge for parcels above 3 kg and up to 5 kg
    # --------------------------------------------------------

    up_to_5kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=200.00
    )

    # --------------------------------------------------------
    # Charge for parcels above 5 kg
    # --------------------------------------------------------

    above_5kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=300.00
    )

    # --------------------------------------------------------
    # Last Updated Time
    # --------------------------------------------------------

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # --------------------------------------------------------
    # String Representation
    # --------------------------------------------------------

    def __str__(self):
        return "SHATHIMART Delivery Charge Rates"

    # --------------------------------------------------------
    # Meta
    # --------------------------------------------------------

    class Meta:
        verbose_name = 'Delivery Charge Rate'
        verbose_name_plural = 'Delivery Charge Rates'

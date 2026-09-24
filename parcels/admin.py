from django.contrib import admin
from django.utils.html import format_html

from .models import Parcel, TrackingHistory


# ============================================================
# PARCEL ADMIN
# ============================================================

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):

    list_display = (
        "tracking_number_display",
        "customer_display",
        "sender_display",
        "receiver_display",
        "parcel_type_display",
        "status_display",
        "delivery_charge_display",
        "created_at_display",
    )

    list_display_links = (
        "tracking_number_display",
    )

    list_filter = (
        "status",
        "parcel_type",
        "pickup_date",
        "delivery_date",
        "created_at",
    )

    search_fields = (
        "tracking_number",
        "customer__username",
        "customer__first_name",
        "customer__last_name",
        "sender_name",
        "sender_phone",
        "receiver_name",
        "receiver_phone",
        "sender_address",
        "receiver_address",
    )

    autocomplete_fields = (
        "customer",
    )

    readonly_fields = (
        "tracking_number",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 20

    date_hierarchy = "created_at"

    fieldsets = (

        # ----------------------------------------------------
        # Customer
        # ----------------------------------------------------

        (
            "Customer Information",
            {
                "fields": (
                    "customer",
                )
            },
        ),

        # ----------------------------------------------------
        # Parcel
        # ----------------------------------------------------

        (
            "Parcel Information",
            {
                "fields": (
                    "tracking_number",
                    "parcel_type",
                    "weight",
                    "description",
                )
            },
        ),

        # ----------------------------------------------------
        # Sender
        # ----------------------------------------------------

        (
            "Sender Information",
            {
                "fields": (
                    "sender_name",
                    "sender_phone",
                    "sender_address",
                )
            },
        ),

        # ----------------------------------------------------
        # Receiver
        # ----------------------------------------------------

        (
            "Receiver Information",
            {
                "fields": (
                    "receiver_name",
                    "receiver_phone",
                    "receiver_address",
                )
            },
        ),

        # ----------------------------------------------------
        # Delivery
        # ----------------------------------------------------

        (
            "Delivery Information",
            {
                "fields": (
                    "pickup_date",
                    "delivery_date",
                    "delivery_charge",
                    "status",
                )
            },
        ),

        # ----------------------------------------------------
        # System
        # ----------------------------------------------------

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    # ========================================================
    # TRACKING NUMBER
    # ========================================================

    @admin.display(
        description="Tracking Number",
        ordering="tracking_number"
    )
    def tracking_number_display(self, obj):

        return format_html(
            '<strong style="color:#2563eb;">{}</strong>',
            obj.tracking_number,
        )

    # ========================================================
    # CUSTOMER
    # ========================================================

    @admin.display(
        description="Customer",
        ordering="customer__username"
    )
    def customer_display(self, obj):

        full_name = obj.customer.get_full_name()

        if full_name:
            return format_html(
                '<strong>{}</strong><br>'
                '<small style="color:#6b7280;">@{}</small>',
                full_name,
                obj.customer.username,
            )

        return obj.customer.username

    # ========================================================
    # SENDER
    # ========================================================

    @admin.display(
        description="Sender",
        ordering="sender_name"
    )
    def sender_display(self, obj):

        return format_html(
            '<strong>{}</strong><br>'
            '<small style="color:#6b7280;">{}</small>',
            obj.sender_name,
            obj.sender_phone,
        )

    # ========================================================
    # RECEIVER
    # ========================================================

    @admin.display(
        description="Receiver",
        ordering="receiver_name"
    )
    def receiver_display(self, obj):

        return format_html(
            '<strong>{}</strong><br>'
            '<small style="color:#6b7280;">{}</small>',
            obj.receiver_name,
            obj.receiver_phone,
        )

    # ========================================================
    # PARCEL TYPE
    # ========================================================

    @admin.display(
        description="Type",
        ordering="parcel_type"
    )
    def parcel_type_display(self, obj):

        return obj.get_parcel_type_display()

    # ========================================================
    # STATUS
    # ========================================================

    @admin.display(
        description="Status",
        ordering="status"
    )
    def status_display(self, obj):

        status_colors = {
            "pending": "#f59e0b",
            "pickup_requested": "#f97316",
            "assigned": "#0ea5e9",
            "picked_up": "#3b82f6",
            "in_transit": "#6366f1",
            "out_for_delivery": "#8b5cf6",
            "delivered": "#10b981",
            "cancelled": "#ef4444",
            "failed": "#dc2626",
            "rescheduled": "#64748b",
        }

        color = status_colors.get(
            obj.status,
            "#6b7280",
        )

        return format_html(
            '<span style="'
            'display:inline-block;'
            'padding:5px 10px;'
            'border-radius:20px;'
            'background:{};'
            'color:white;'
            'font-size:12px;'
            'font-weight:600;'
            '">'
            '{}'
            '</span>',
            color,
            obj.get_status_display(),
        )

    # ========================================================
    # DELIVERY CHARGE
    # ========================================================

    @admin.display(
        description="Charge",
        ordering="delivery_charge"
    )
    def delivery_charge_display(self, obj):

        return format_html(
            '<strong>Rs. {}</strong>',
            obj.delivery_charge,
        )

    # ========================================================
    # CREATED
    # ========================================================

    @admin.display(
        description="Created",
        ordering="created_at"
    )
    def created_at_display(self, obj):

        return obj.created_at.strftime(
            "%Y-%m-%d %H:%M"
        )


# ============================================================
# TRACKING HISTORY ADMIN
# ============================================================

@admin.register(TrackingHistory)
class TrackingHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "parcel_display",
        "status_display",
        "location_display",
        "remarks_display",
        "created_at_display",
    )

    list_display_links = (
        "parcel_display",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "parcel__tracking_number",
        "parcel__sender_name",
        "parcel__receiver_name",
        "location",
        "remarks",
    )

    autocomplete_fields = (
        "parcel",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25

    date_hierarchy = "created_at"

    fieldsets = (

        # ----------------------------------------------------
        # Tracking
        # ----------------------------------------------------

        (
            "Tracking Information",
            {
                "fields": (
                    "parcel",
                    "status",
                    "location",
                    "remarks",
                )
            },
        ),

        # ----------------------------------------------------
        # System
        # ----------------------------------------------------

        (
            "System Information",
            {
                "fields": (
                    "created_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    # ========================================================
    # PARCEL
    # ========================================================

    @admin.display(
        description="Parcel"
    )
    def parcel_display(self, obj):

        return format_html(
            '<strong style="color:#2563eb;">{}</strong>',
            obj.parcel.tracking_number,
        )

    # ========================================================
    # STATUS
    # ========================================================

    @admin.display(
        description="Status",
        ordering="status"
    )
    def status_display(self, obj):

        status_colors = {
            "pending": "#f59e0b",
            "pickup_requested": "#f97316",
            "assigned": "#0ea5e9",
            "picked_up": "#3b82f6",
            "in_transit": "#6366f1",
            "out_for_delivery": "#8b5cf6",
            "delivered": "#10b981",
            "cancelled": "#ef4444",
            "failed": "#dc2626",
            "rescheduled": "#64748b",
        }

        color = status_colors.get(
            obj.status,
            "#6b7280",
        )

        return format_html(
            '<span style="'
            'display:inline-block;'
            'padding:5px 10px;'
            'border-radius:20px;'
            'background:{};'
            'color:white;'
            'font-size:12px;'
            'font-weight:600;'
            '">'
            '{}'
            '</span>',
            color,
            obj.get_status_display(),
        )

    # ========================================================
    # LOCATION
    # ========================================================

    @admin.display(
        description="Location"
    )
    def location_display(self, obj):

        return obj.location or "-"

    # ========================================================
    # REMARKS
    # ========================================================

    @admin.display(
        description="Remarks"
    )
    def remarks_display(self, obj):

        remarks = obj.remarks or "-"

        if len(remarks) > 50:
            remarks = remarks[:50] + "..."

        return remarks

    # ========================================================
    # CREATED
    # ========================================================

    @admin.display(
        description="Created",
        ordering="created_at"
    )
    def created_at_display(self, obj):

        return obj.created_at.strftime(
            "%Y-%m-%d %H:%M"
        )
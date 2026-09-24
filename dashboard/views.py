from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomerProfile
from parcels.models import (
    Parcel,
    TrackingHistory,
    DeliveryChargeRate,
)
from parcels.utils import (
    calculate_delivery_charge,
    get_delivery_charge_rates,
)
from deliveries.models import Delivery
from notifications.models import Notification
from payments.models import Payment


# ============================================================
# ADMIN ACCESS HELPER
# ============================================================

def admin_required(request):

    if not request.user.is_authenticated:
        return False

    if request.user.is_superuser:
        return True

    try:
        return request.user.profile.role == "admin"

    except CustomerProfile.DoesNotExist:
        return False


# ============================================================
# ADMIN ACCESS CHECK
# ============================================================

def check_admin(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not admin_required(request):

        messages.error(
            request,
            "Administrator access required."
        )

        return redirect("admin_login")

    return None


# ============================================================
# CREATE CUSTOMER NOTIFICATION
# ============================================================

def create_customer_notification(
    parcel,
    title,
    message
):

    if not parcel:
        return None

    if not parcel.customer:
        return None

    customer = parcel.customer

    if hasattr(customer, "user"):
        user = customer.user
    else:
        user = customer

    if not user:
        return None

    return Notification.objects.create(
        user=user,
        parcel=parcel,
        title=title,
        message=message,
        is_read=False
    )


# ============================================================
# STATUS NOTIFICATION MESSAGE
# ============================================================

def get_status_notification_message(parcel):

    status_messages = {

        "pending":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"has been received and is waiting "
                f"for processing."
            ),

        "pickup_requested":
            (
                f"Pickup has been requested for "
                f"your parcel "
                f"{parcel.tracking_number}."
            ),

        "assigned":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"has been assigned to a delivery "
                f"staff member."
            ),

        "picked_up":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"has been picked up."
            ),

        "in_transit":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"is currently in transit."
            ),

        "out_for_delivery":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"is out for delivery."
            ),

        "delivered":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"has been successfully delivered."
            ),

        "cancelled":
            (
                f"Your parcel "
                f"{parcel.tracking_number} "
                f"delivery has been cancelled."
            ),

        "failed":
            (
                f"Delivery of your parcel "
                f"{parcel.tracking_number} "
                f"was unsuccessful."
            ),

        "rescheduled":
            (
                f"Delivery of your parcel "
                f"{parcel.tracking_number} "
                f"has been rescheduled."
            ),
    }

    return status_messages.get(
        parcel.status,
        (
            f"Your parcel "
            f"{parcel.tracking_number} "
            f"status has been updated."
        )
    )


# ============================================================
# SEND STATUS NOTIFICATION
# ============================================================

def notify_parcel_status(parcel):

    status_display = parcel.get_status_display()

    title = (
        f"Parcel Status: "
        f"{status_display}"
    )

    message = get_status_notification_message(
        parcel
    )

    return create_customer_notification(
        parcel=parcel,
        title=title,
        message=message
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@login_required(login_url="login")
def admin_dashboard(request):

    profile, created = CustomerProfile.objects.get_or_create(

        user=request.user,

        defaults={
            "role": (
                "admin"
                if request.user.is_superuser
                else "customer"
            )
        }
    )

    # --------------------------------------------------------
    # SUPERUSER
    # --------------------------------------------------------

    if request.user.is_superuser:

        if profile.role != "admin":

            profile.role = "admin"

            profile.save(
                update_fields=["role"]
            )

    # --------------------------------------------------------
    # NORMAL ADMIN
    # --------------------------------------------------------

    elif profile.role != "admin":

        messages.error(
            request,
            "Access denied. Administrator access required."
        )

        logout(request)

        return redirect("admin_login")

    # --------------------------------------------------------
    # PARCEL DATA
    # --------------------------------------------------------

    parcels = (
        Parcel.objects
        .select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        )
        .all()
        .order_by("-created_at")
    )

    # --------------------------------------------------------
    # PARCEL COUNTS
    # --------------------------------------------------------

    total_parcels = parcels.count()

    pending_count = parcels.filter(
        status="pending"
    ).count()

    pickup_requested_count = parcels.filter(
        status="pickup_requested"
    ).count()

    assigned_count = parcels.filter(
        status="assigned"
    ).count()

    picked_up_count = parcels.filter(
        status="picked_up"
    ).count()

    in_transit_count = parcels.filter(
        status="in_transit"
    ).count()

    out_for_delivery_count = parcels.filter(
        status="out_for_delivery"
    ).count()

    delivered_count = parcels.filter(
        status="delivered"
    ).count()

    cancelled_count = parcels.filter(
        status="cancelled"
    ).count()

    failed_count = parcels.filter(
        status="failed"
    ).count()

    rescheduled_count = parcels.filter(
        status="rescheduled"
    ).count()

    # --------------------------------------------------------
    # RECENT PARCELS
    # --------------------------------------------------------

    recent_parcels = parcels[:10]

    # --------------------------------------------------------
    # RECENT TRACKING
    # --------------------------------------------------------

    recent_tracking = (
        TrackingHistory.objects
        .select_related(
            "parcel",
            "parcel__customer",
            "parcel__delivery",
            "parcel__delivery__delivery_staff",
        )
        .order_by("-created_at")[:10]
    )

    # --------------------------------------------------------
    # ADMIN UNREAD NOTIFICATIONS
    # --------------------------------------------------------

    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "profile": profile,

        "parcels": parcels,

        "total_parcels":
            total_parcels,

        "pending_count":
            pending_count,

        "pickup_requested_count":
            pickup_requested_count,

        "assigned_count":
            assigned_count,

        "picked_up_count":
            picked_up_count,

        "in_transit_count":
            in_transit_count,

        "out_for_delivery_count":
            out_for_delivery_count,

        "delivered_count":
            delivered_count,

        "cancelled_count":
            cancelled_count,

        "failed_count":
            failed_count,

        "rescheduled_count":
            rescheduled_count,

        "recent_parcels":
            recent_parcels,

        "recent_tracking":
            recent_tracking,

        "unread_notifications":
            unread_notifications,
    }

    return render(
        request,
        "dashboard/admin_dashboard.html",
        context
    )


# ============================================================
# DELIVERY STAFF DASHBOARD
# ============================================================

@login_required(login_url="login")
def staff_dashboard(request):

    profile, created = CustomerProfile.objects.get_or_create(

        user=request.user,

        defaults={
            "role": "customer"
        }
    )

    # --------------------------------------------------------
    # SUPERUSER
    # --------------------------------------------------------

    if request.user.is_superuser:

        if profile.role != "admin":

            profile.role = "admin"

            profile.save(
                update_fields=["role"]
            )

        return redirect("admin_dashboard")

    # --------------------------------------------------------
    # DELIVERY STAFF ACCESS
    # --------------------------------------------------------

    if profile.role != "delivery_staff":

        messages.error(
            request,
            "Access denied. Delivery staff access required."
        )

        logout(request)

        return redirect("staff_login")

    # --------------------------------------------------------
    # ONLY ASSIGNED PARCELS
    # --------------------------------------------------------

    parcels = (
        Parcel.objects
        .filter(
            delivery__delivery_staff=request.user
        )
        .select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        )
        .order_by("-updated_at")
    )

    # --------------------------------------------------------
    # ACTIVE STATUSES
    # --------------------------------------------------------

    active_statuses = [
        "assigned",
        "picked_up",
        "in_transit",
        "out_for_delivery",
    ]

    # --------------------------------------------------------
    # ACTIVE PARCEL COUNT
    # --------------------------------------------------------

    total_parcels = parcels.filter(
        status__in=active_statuses
    ).count()

    # --------------------------------------------------------
    # STATUS COUNTS
    # --------------------------------------------------------

    assigned_count = parcels.filter(
        status="assigned"
    ).count()

    picked_up_count = parcels.filter(
        status="picked_up"
    ).count()

    in_transit_count = parcels.filter(
        status="in_transit"
    ).count()

    out_for_delivery_count = parcels.filter(
        status="out_for_delivery"
    ).count()

    # --------------------------------------------------------
    # RECENT ACTIVE PARCELS
    # --------------------------------------------------------

    recent_parcels = (
        parcels
        .filter(
            status__in=active_statuses
        )
        .order_by("-updated_at")[:10]
    )

    context = {

        "profile": profile,

        "parcels": parcels,

        "recent_parcels":
            recent_parcels,

        "total_parcels":
            total_parcels,

        "assigned_count":
            assigned_count,

        "picked_up_count":
            picked_up_count,

        "in_transit_count":
            in_transit_count,

        "out_for_delivery_count":
            out_for_delivery_count,
    }

    return render(
        request,
        "dashboard/staff_dashboard.html",
        context
    )


# ============================================================
# DELIVERY STAFF - PROFILE
# ============================================================

@login_required(login_url="staff_login")
def staff_profile(request):

    profile = get_object_or_404(
        CustomerProfile,
        user=request.user
    )

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    if profile.role != "delivery_staff":

        messages.error(
            request,
            "Access denied. Delivery staff access required."
        )

        logout(request)

        return redirect("staff_login")

    context = {
        "profile": profile,
    }

    return render(
        request,
        "dashboard/staff_profile.html",
        context
    )


# ============================================================
# DELIVERY STAFF - MY PARCELS
# ============================================================

@login_required(login_url="staff_login")
def staff_parcels(request):

    profile = get_object_or_404(
        CustomerProfile,
        user=request.user
    )

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    if profile.role != "delivery_staff":

        messages.error(
            request,
            "Access denied. Delivery staff access required."
        )

        logout(request)

        return redirect("staff_login")

    parcels = (
        Parcel.objects
        .filter(
            delivery__delivery_staff=request.user
        )
        .select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        )
        .order_by("-updated_at")
    )

    context = {

        "profile": profile,

        "parcels": parcels,

        "total_parcels":
            parcels.count(),
    }

    return render(
        request,
        "dashboard/staff_parcels.html",
        context
    )


# ============================================================
# DELIVERY STAFF - PARCEL DETAIL / UPDATE
# ============================================================

@login_required(login_url="staff_login")
def staff_parcel_detail(
    request,
    parcel_id
):

    profile = get_object_or_404(
        CustomerProfile,
        user=request.user
    )

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    if profile.role != "delivery_staff":

        messages.error(
            request,
            "Access denied. Delivery staff access required."
        )

        logout(request)

        return redirect("staff_login")

    parcel = get_object_or_404(

        Parcel.objects.select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        ),

        id=parcel_id,

        delivery__delivery_staff=request.user,
    )

    try:

        delivery = parcel.delivery

    except Delivery.DoesNotExist:

        messages.error(
            request,
            "Delivery record was not found for this parcel."
        )

        return redirect("staff_parcels")

    # ========================================================
    # CURRENT PAYMENT
    # ========================================================

    payment = Payment.objects.filter(
        parcel=parcel
    ).first()

    # ========================================================
    # UPDATE PARCEL + PAYMENT
    # ========================================================

    if request.method == "POST":

        # ----------------------------------------------------
        # DELIVERY STATUS
        # ----------------------------------------------------

        new_status = request.POST.get(
            "status",
            ""
        ).strip()

        # ----------------------------------------------------
        # PAYMENT STATUS
        # ----------------------------------------------------

        new_payment_status = request.POST.get(
            "payment_status",
            "pending"
        ).strip()

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        location = request.POST.get(
            "location",
            ""
        ).strip()

        # ----------------------------------------------------
        # REMARKS
        # ----------------------------------------------------

        remarks = request.POST.get(
            "remarks",
            ""
        ).strip()

        # ====================================================
        # VALID DELIVERY STATUS
        # ====================================================

        allowed_statuses = {
            "assigned",
            "picked_up",
            "in_transit",
            "out_for_delivery",
            "delivered",
            "failed",
            "rescheduled",
        }

        if new_status not in allowed_statuses:

            messages.error(
                request,
                "Invalid delivery status selected."
            )

            return redirect(
                "staff_parcel_detail",
                parcel_id=parcel.id
            )

        # ====================================================
        # VALID PAYMENT STATUS
        # ====================================================

        allowed_payment_statuses = {
            "pending",
            "paid",
            "failed",
            "refunded",
        }

        if new_payment_status not in allowed_payment_statuses:

            messages.error(
                request,
                "Invalid payment status selected."
            )

            return redirect(
                "staff_parcel_detail",
                parcel_id=parcel.id
            )

        # ====================================================
        # OLD DELIVERY STATUS
        # ====================================================

        old_status = parcel.status

        # ====================================================
        # OLD PAYMENT STATUS
        # ====================================================

        old_payment_status = (
            payment.payment_status
            if payment
            else "pending"
        )

        # ====================================================
        # UPDATE PARCEL STATUS
        # ====================================================

        parcel.status = new_status

        # ====================================================
        # DELIVERY DATE
        # ====================================================

        if new_status == "delivered":

            parcel.delivery_date = (
                timezone.now().date()
            )

        parcel.save()

        # ====================================================
        # UPDATE DELIVERY
        # ====================================================

        delivery.status = new_status
        delivery.delivery_staff = request.user

        # ====================================================
        # PICKUP TIME
        # ====================================================

        if (
            new_status == "picked_up"
            and delivery.pickup_time is None
        ):

            delivery.pickup_time = timezone.now()

        # ====================================================
        # DELIVERY TIME
        # ====================================================

        if new_status == "delivered":

            if delivery.delivery_time is None:

                delivery.delivery_time = timezone.now()

        # ====================================================
        # REMARKS
        # ====================================================

        if remarks:

            delivery.remarks = remarks

        delivery.save()

        # ====================================================
        # CREATE / UPDATE PAYMENT
        # ====================================================

        payment, payment_created = (
            Payment.objects.get_or_create(

                parcel=parcel,

                defaults={
                    "amount": (
                        parcel.delivery_charge
                        or 0
                    ),
                    "payment_method": "cod",
                    "payment_status": "pending",
                }
            )
        )

        # Always keep payment amount synchronized
        # with the parcel delivery charge.

        payment.amount = (
            parcel.delivery_charge
            or 0
        )

        payment.payment_method = "cod"

        # ====================================================
        # UPDATE PAYMENT STATUS
        # ====================================================

        payment.payment_status = new_payment_status

        # ====================================================
        # PAID TIME
        # ====================================================

        if new_payment_status == "paid":

            if payment.paid_at is None:

                payment.paid_at = timezone.now()

        else:

            payment.paid_at = None

        payment.save()

        # ====================================================
        # TRACKING HISTORY
        # ====================================================

        if (
            old_status != new_status
            or location
            or remarks
        ):

            if remarks:

                tracking_remarks = remarks

            else:

                tracking_remarks = (
                    f"Delivery status updated to "
                    f"{parcel.get_status_display()}."
                )

            TrackingHistory.objects.create(

                parcel=parcel,

                status=new_status,

                location=location,

                remarks=tracking_remarks
            )

        # ====================================================
        # CUSTOMER STATUS NOTIFICATION
        # ====================================================

        if old_status != new_status:

            notify_parcel_status(
                parcel
            )

        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        if (
            old_status != new_status
            and old_payment_status != new_payment_status
        ):

            messages.success(
                request,
                (
                    f"Parcel {parcel.tracking_number} "
                    f"status changed to "
                    f"{parcel.get_status_display()} "
                    f"and payment status changed to "
                    f"{payment.get_payment_status_display()}."
                )
            )

        elif old_status != new_status:

            messages.success(
                request,
                (
                    f"Parcel {parcel.tracking_number} "
                    f"status changed from "
                    f"{old_status.replace('_', ' ').title()} "
                    f"to "
                    f"{parcel.get_status_display()}."
                )
            )

        elif old_payment_status != new_payment_status:

            messages.success(
                request,
                (
                    f"Payment status for "
                    f"{parcel.tracking_number} "
                    f"changed to "
                    f"{payment.get_payment_status_display()}."
                )
            )

        else:

            messages.success(
                request,
                (
                    f"Parcel {parcel.tracking_number} "
                    f"updated successfully."
                )
            )

        return redirect(
            "staff_parcel_detail",
            parcel_id=parcel.id
        )

    # ========================================================
    # TRACKING HISTORY
    # ========================================================

    tracking_history = (
        parcel.tracking_history
        .all()
        .order_by("-created_at")
    )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        "profile":
            profile,

        "parcel":
            parcel,

        "delivery":
            delivery,

        "payment":
            payment,

        "tracking_history":
            tracking_history,

        "status_choices":
            Delivery.STATUS_CHOICES,

    }

    return render(
        request,
        "dashboard/staff_parcel_detail.html",
        context
    )


# ============================================================
# PARCEL MANAGEMENT
# ============================================================

@login_required(login_url="login")
def parcel_management(request):

    access = check_admin(request)

    if access:
        return access

    parcels = (
        Parcel.objects
        .select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        )
        .order_by("-created_at")
    )

    context = {

        "profile":
            request.user.profile,

        "parcels":
            parcels,

        "total_parcels":
            parcels.count(),
    }

    return render(
        request,
        "dashboard/parcel_management.html",
        context
    )


# ============================================================
# TRACKING MANAGEMENT
# ============================================================

@login_required(login_url="login")
def tracking_management(request):

    access = check_admin(request)

    if access:
        return access

    parcels = (
        Parcel.objects
        .select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        )
        .order_by("-updated_at")
    )

    context = {

        "profile":
            request.user.profile,

        "parcels":
            parcels,

        "total_parcels":
            parcels.count(),
    }

    return render(
        request,
        "dashboard/tracking_management.html",
        context
    )


# ============================================================
# ADMIN - VIEW ONE PARCEL TRACKING
# ============================================================

@login_required(login_url="login")
def parcel_tracking(request, parcel_id):

    access = check_admin(request)

    if access:
        return access

    # --------------------------------------------------------
    # GET PARCEL
    # --------------------------------------------------------

    parcel = get_object_or_404(

        Parcel.objects.select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        ),

        id=parcel_id
    )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    payment = (
        Payment.objects
        .filter(parcel=parcel)
        .first()
    )

    # --------------------------------------------------------
    # TRACKING HISTORY
    # --------------------------------------------------------

    tracking_history = (
        TrackingHistory.objects
        .filter(
            parcel=parcel
        )
        .order_by("-created_at")
    )

    # --------------------------------------------------------
    # TOTAL TRACKING UPDATES
    # --------------------------------------------------------

    total_tracking = tracking_history.count()

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "profile":
            request.user.profile,

        "parcel":
            parcel,

        "payment":
            payment,

        "tracking_history":
            tracking_history,

        "total_tracking":
            total_tracking,
    }

    return render(
        request,
        "dashboard/parcel_tracking.html",
        context
    )


# ============================================================
# DELIVERY MANAGEMENT
# ============================================================

@login_required(login_url="login")
def delivery_management(request):

    access = check_admin(request)

    if access:
        return access

    parcels = (
        Parcel.objects
        .select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        )
        .filter(
            status__in=[
                "assigned",
                "picked_up",
                "in_transit",
                "out_for_delivery",
                "delivered",
                "failed",
                "rescheduled",
            ]
        )
        .order_by("-updated_at")
    )

    delivery_staff = (
        User.objects
        .filter(
            profile__role="delivery_staff",
            is_active=True,
        )
        .select_related("profile")
        .order_by(
            "first_name",
            "last_name",
            "username",
        )
    )

    context = {

        "profile":
            request.user.profile,

        "parcels":
            parcels,

        "delivery_staff":
            delivery_staff,

        "total_deliveries":
            parcels.count(),
    }

    return render(
        request,
        "dashboard/delivery_management.html",
        context
    )


# ============================================================
# ASSIGN / REASSIGN DELIVERY STAFF
# ============================================================

@login_required(login_url="login")
def assign_delivery_staff(
    request,
    parcel_id
):

    access = check_admin(request)

    if access:
        return access

    if request.method != "POST":

        messages.error(
            request,
            "Invalid request."
        )

        return redirect(
            "admin_deliveries"
        )

    parcel = get_object_or_404(
        Parcel.objects.select_related(
            "customer",
            "delivery",
            "delivery__delivery_staff",
        ),
        id=parcel_id
    )

    staff_id = request.POST.get(
        "delivery_staff"
    )

    if not staff_id:

        messages.error(
            request,
            "Please select a delivery staff member."
        )

        return redirect(
            "admin_deliveries"
        )

    try:

        staff = (
            User.objects
            .select_related("profile")
            .get(
                id=staff_id,
                profile__role="delivery_staff",
                is_active=True,
            )
        )

    except User.DoesNotExist:

        messages.error(
            request,
            "Invalid delivery staff selected."
        )

        return redirect(
            "admin_deliveries"
        )

    delivery, created = (
        Delivery.objects.get_or_create(
            parcel=parcel
        )
    )

    old_staff = delivery.delivery_staff
    old_status = parcel.status

    delivery.delivery_staff = staff

    if parcel.status in [
        "pending",
        "pickup_requested",
    ]:

        parcel.status = "assigned"

    delivery.status = parcel.status

    delivery.save()
    parcel.save()

    staff_name = (
        staff.get_full_name()
        or staff.username
    )

    # --------------------------------------------------------
    # TRACKING HISTORY
    # --------------------------------------------------------

    if old_staff and old_staff.id != staff.id:

        old_staff_name = (
            old_staff.get_full_name()
            or old_staff.username
        )

        remarks = (
            f"Delivery staff reassigned from "
            f"{old_staff_name} to {staff_name}."
        )

    else:

        remarks = (
            f"Parcel assigned to delivery staff "
            f"{staff_name}."
        )

    TrackingHistory.objects.create(
        parcel=parcel,
        status=parcel.status,
        remarks=remarks
    )

    # --------------------------------------------------------
    # CUSTOMER NOTIFICATION
    # --------------------------------------------------------

    if old_status != parcel.status:

        notify_parcel_status(
            parcel
        )

    elif (
        old_staff is None
        or old_staff.id != staff.id
    ):

        create_customer_notification(
            parcel=parcel,
            title="Delivery Staff Assigned",
            message=(
                f"Delivery staff "
                f"{staff_name} "
                f"has been assigned to your parcel "
                f"{parcel.tracking_number}."
            )
        )

    # --------------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------------

    if (
        old_staff
        and old_staff.id != staff.id
    ):

        messages.success(
            request,
            f"Parcel {parcel.tracking_number} "
            f"reassigned to {staff_name}."
        )

    else:

        messages.success(
            request,
            f"Parcel {parcel.tracking_number} "
            f"assigned to {staff_name}."
        )

    return redirect(
        "admin_deliveries"
    )


# ============================================================
# DELIVERY CHARGE MANAGEMENT
# ============================================================

@login_required(login_url="login")
def delivery_charge_management(request):

    access = check_admin(request)

    if access:
        return access

    # --------------------------------------------------------
    # GET CURRENT DELIVERY CHARGE RATES
    # --------------------------------------------------------

    rates = get_delivery_charge_rates()

    # --------------------------------------------------------
    # UPDATE DELIVERY CHARGE RATES
    # --------------------------------------------------------

    if request.method == "POST":

        up_to_1kg = request.POST.get(
            "up_to_1kg",
            ""
        ).strip()

        up_to_3kg = request.POST.get(
            "up_to_3kg",
            ""
        ).strip()

        up_to_5kg = request.POST.get(
            "up_to_5kg",
            ""
        ).strip()

        above_5kg = request.POST.get(
            "above_5kg",
            ""
        ).strip()

        # ----------------------------------------------------
        # CONVERT TO DECIMAL
        # ----------------------------------------------------

        try:

            rate_1kg = Decimal(
                up_to_1kg
            )

            rate_3kg = Decimal(
                up_to_3kg
            )

            rate_5kg = Decimal(
                up_to_5kg
            )

            rate_above_5kg = Decimal(
                above_5kg
            )

        except (
            InvalidOperation,
            ValueError
        ):

            messages.error(
                request,
                "Please enter valid delivery charge amounts."
            )

            return redirect(
                "delivery_charge_management"
            )

        # ----------------------------------------------------
        # NEGATIVE VALUE CHECK
        # ----------------------------------------------------

        if (
            rate_1kg < 0
            or rate_3kg < 0
            or rate_5kg < 0
            or rate_above_5kg < 0
        ):

            messages.error(
                request,
                "Delivery charges cannot be negative."
            )

            return redirect(
                "delivery_charge_management"
            )

        # ----------------------------------------------------
        # SAVE RATES
        # ----------------------------------------------------

        rates.up_to_1kg = rate_1kg
        rates.up_to_3kg = rate_3kg
        rates.up_to_5kg = rate_5kg
        rates.above_5kg = rate_above_5kg

        rates.save()

        messages.success(
            request,
            "Delivery charges updated successfully."
        )

        return redirect(
            "delivery_charge_management"
        )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "profile":
            request.user.profile,

        "rates":
            rates,
    }

    return render(
        request,
        "dashboard/delivery_charges.html",
        context
    )


# ============================================================
# CUSTOMER MANAGEMENT
# ============================================================

@login_required(login_url="login")
def customer_management(request):

    access = check_admin(request)

    if access:
        return access

    customers = (
        CustomerProfile.objects
        .select_related("user")
        .filter(
            role="customer"
        )
        .order_by("-created_at")
    )

    context = {

        "profile":
            request.user.profile,

        "customers":
            customers,

        "total_customers":
            customers.count(),
    }

    return render(
        request,
        "dashboard/customer_management.html",
        context
    )


# ============================================================
# DELIVERY STAFF MANAGEMENT
# ============================================================

@login_required(login_url="login")
def staff_management(request):

    access = check_admin(request)

    if access:
        return access

    # ========================================================
    # CREATE DELIVERY STAFF
    # ========================================================

    if request.method == "POST":

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        username = request.POST.get(
            "username",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not first_name:

            messages.error(
                request,
                "First name is required."
            )

            return redirect(
                "admin_staff"
            )

        if not username:

            messages.error(
                request,
                "Username is required."
            )

            return redirect(
                "admin_staff"
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():

            messages.error(
                request,
                "This username is already registered."
            )

            return redirect(
                "admin_staff"
            )

        if email:

            if User.objects.filter(
                email__iexact=email
            ).exists():

                messages.error(
                    request,
                    "This email address is already registered."
                )

                return redirect(
                    "admin_staff"
                )

        if not password:

            messages.error(
                request,
                "Password is required."
            )

            return redirect(
                "admin_staff"
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect(
                "admin_staff"
            )

        if len(password) < 8:

            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

            return redirect(
                "admin_staff"
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        CustomerProfile.objects.create(
            user=user,
            phone=phone,
            address=address,
            city=city,
            role="delivery_staff"
        )

        messages.success(
            request,
            f"Delivery staff '{username}' "
            f"created successfully."
        )

        return redirect(
            "admin_staff"
        )

    # ========================================================
    # DELIVERY STAFF LIST
    # ========================================================

    staff = (
        CustomerProfile.objects
        .select_related("user")
        .filter(
            role="delivery_staff"
        )
        .order_by("-created_at")
    )

    context = {

        "profile":
            request.user.profile,

        "staff":
            staff,

        "total_staff":
            staff.count(),
    }

    return render(
        request,
        "dashboard/staff_management.html",
        context
    )


# ============================================================
# ADMINISTRATOR MANAGEMENT
# ============================================================

@login_required(login_url="login")
def administrator_management(request):

    access = check_admin(request)

    if access:
        return access

    administrators = (
        CustomerProfile.objects
        .select_related("user")
        .filter(
            role="admin"
        )
        .order_by("-created_at")
    )

    context = {

        "profile":
            request.user.profile,

        "administrators":
            administrators,

        "total_admins":
            administrators.count(),
    }

    return render(
        request,
        "dashboard/administrator_management.html",
        context
    )


# ============================================================
# ADMINISTRATOR PROFILE
# ============================================================

@login_required(login_url="login")
def administrator_profile(
    request,
    user_id
):

    access = check_admin(request)

    if access:
        return access

    administrator = get_object_or_404(
        CustomerProfile.objects.select_related(
            "user"
        ),
        user_id=user_id,
        role="admin"
    )

    context = {

        "profile":
            request.user.profile,

        "administrator":
            administrator,
    }

    return render(
        request,
        "dashboard/administrator_profile.html",
        context
    )


# ============================================================
# REPORTS
# ============================================================

@login_required(login_url="login")
def reports(request):

    access = check_admin(request)

    if access:
        return access

    parcels = Parcel.objects.all()

    # --------------------------------------------------------
    # PARCEL COUNTS
    # --------------------------------------------------------

    total_parcels = parcels.count()

    pending_count = parcels.filter(
        status="pending"
    ).count()

    pickup_requested_count = parcels.filter(
        status="pickup_requested"
    ).count()

    assigned_count = parcels.filter(
        status="assigned"
    ).count()

    picked_up_count = parcels.filter(
        status="picked_up"
    ).count()

    in_transit_count = parcels.filter(
        status="in_transit"
    ).count()

    out_for_delivery_count = parcels.filter(
        status="out_for_delivery"
    ).count()

    delivered_count = parcels.filter(
        status="delivered"
    ).count()

    cancelled_count = parcels.filter(
        status="cancelled"
    ).count()

    failed_count = parcels.filter(
        status="failed"
    ).count()

    rescheduled_count = parcels.filter(
        status="rescheduled"
    ).count()

    # --------------------------------------------------------
    # USER COUNTS
    # --------------------------------------------------------

    total_customers = (
        CustomerProfile.objects
        .filter(
            role="customer"
        )
        .count()
    )

    total_staff = (
        CustomerProfile.objects
        .filter(
            role="delivery_staff"
        )
        .count()
    )

    total_admins = (
        CustomerProfile.objects
        .filter(
            role="admin"
        )
        .count()
    )

    # --------------------------------------------------------
    # NOTIFICATION COUNT
    # --------------------------------------------------------

    total_notifications = (
        Notification.objects.count()
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        "profile":
            request.user.profile,

        "total_parcels":
            total_parcels,

        "pending_count":
            pending_count,

        "pickup_requested_count":
            pickup_requested_count,

        "assigned_count":
            assigned_count,

        "picked_up_count":
            picked_up_count,

        "in_transit_count":
            in_transit_count,

        "out_for_delivery_count":
            out_for_delivery_count,

        "delivered_count":
            delivered_count,

        "cancelled_count":
            cancelled_count,

        "failed_count":
            failed_count,

        "rescheduled_count":
            rescheduled_count,

        "total_customers":
            total_customers,

        "total_staff":
            total_staff,

        "total_admins":
            total_admins,

        "total_notifications":
            total_notifications,
    }

    return render(
        request,
        "dashboard/reports.html",
        context
    )
# ============================================================
# SHATHIMART PARCEL VIEWS
# File: parcels/views.py
# ============================================================

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Parcel, TrackingHistory
from .utils import (
    calculate_delivery_charge,
    get_delivery_charge_rates,
)

from payments.models import Payment


# ============================================================
# TRACKING NUMBER GENERATOR
# ============================================================

def generate_tracking_number():
    """
    Generate a unique tracking number for a parcel.

    Example:

        TRK202609240001
        TRK202609240002
        TRK202609240003

    The number contains:

        TRK
        YYYYMMDD
        4-digit sequence number
    """

    # Get today's date in YYYYMMDD format.
    today = timezone.localdate().strftime("%Y%m%d")

    # Example:
    # TRK20260924
    prefix = f"TRK{today}"

    # Find the latest parcel created today.
    last_parcel = (
        Parcel.objects
        .filter(
            tracking_number__startswith=prefix
        )
        .order_by("-id")
        .first()
    )

    # --------------------------------------------------------
    # If a parcel already exists today, increase its number.
    # --------------------------------------------------------

    if last_parcel:

        try:

            last_number = int(
                last_parcel.tracking_number[-4:]
            )

        except (
            ValueError,
            TypeError
        ):

            last_number = 0

        next_number = last_number + 1

    # --------------------------------------------------------
    # If this is the first parcel today.
    # --------------------------------------------------------

    else:

        next_number = 1

    # Example:
    # TRK202609240001
    return f"{prefix}{next_number:04d}"


# ============================================================
# TRACKING HISTORY
# ============================================================

def create_tracking_history(
    parcel,
    status=None,
    location="",
    remarks=""
):
    """
    Create a tracking history entry for a parcel.

    If status is not supplied, the current parcel status
    will be used.
    """

    # Use current parcel status if no status was supplied.
    if status is None:
        status = parcel.status

    TrackingHistory.objects.create(

        parcel=parcel,

        status=status,

        location=location,

        remarks=remarks

    )


# ============================================================
# CUSTOMER PARCEL LIST
# ============================================================

@login_required
def parcel_list(request):
    """
    Display all parcels belonging to the currently logged-in
    customer.
    """

    parcels = (
        Parcel.objects
        .filter(
            customer=request.user
        )
        .select_related(
            "delivery",
            "delivery__delivery_staff",
            "payment"
        )
        .order_by(
            "-created_at"
        )
    )

    return render(

        request,

        "parcels/parcel_list.html",

        {
            "parcels": parcels
        }

    )


# ============================================================
# CREATE PARCEL
# ============================================================

@login_required
def create_parcel(request):
    """
    Create a new parcel.

    Delivery charge is NOT accepted from the browser.

    Instead:

        Parcel Weight
                ↓
        calculate_delivery_charge()
                ↓
        Admin-configured DeliveryChargeRate
                ↓
        Final Delivery Charge
                ↓
        Parcel + Payment

    This prevents customers from changing the delivery charge
    using browser developer tools.
    """

    # --------------------------------------------------------
    # Get current admin-configured delivery rates.
    #
    # This is also sent to the Create Parcel template so that
    # the frontend can display the current rates.
    # --------------------------------------------------------

    rates = get_delivery_charge_rates()

    # ========================================================
    # POST REQUEST
    # ========================================================

    if request.method == "POST":

        # ----------------------------------------------------
        # GET FORM DATA
        # ----------------------------------------------------

        sender_name = request.POST.get(
            "sender_name",
            ""
        ).strip()

        sender_phone = request.POST.get(
            "sender_phone",
            ""
        ).strip()

        sender_address = request.POST.get(
            "sender_address",
            ""
        ).strip()

        receiver_name = request.POST.get(
            "receiver_name",
            ""
        ).strip()

        receiver_phone = request.POST.get(
            "receiver_phone",
            ""
        ).strip()

        receiver_address = request.POST.get(
            "receiver_address",
            ""
        ).strip()

        parcel_type = request.POST.get(
            "parcel_type",
            "package"
        ).strip()

        weight = request.POST.get(
            "weight",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        pickup_date = (
            request.POST.get("pickup_date")
            or None
        )

        delivery_date = (
            request.POST.get("delivery_date")
            or None
        )

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        #
        # There is intentionally NO payment_method here.
        #
        # The system automatically uses:
        #
        # payment_method = COD
        # payment_status = Pending
        #
        # Payment can later be updated by authorized staff.
        # ----------------------------------------------------


        # ====================================================
        # REQUIRED FIELD VALIDATION
        # ====================================================

        if not sender_name:

            messages.error(
                request,
                "Please enter the sender name."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        if not sender_phone:

            messages.error(
                request,
                "Please enter the sender phone number."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        if not sender_address:

            messages.error(
                request,
                "Please enter the sender address."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        if not receiver_name:

            messages.error(
                request,
                "Please enter the receiver name."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        if not receiver_phone:

            messages.error(
                request,
                "Please enter the receiver phone number."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        if not receiver_address:

            messages.error(
                request,
                "Please enter the receiver address."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        if not weight:

            messages.error(
                request,
                "Please enter the parcel weight."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        # ====================================================
        # WEIGHT VALIDATION
        # ====================================================

        try:

            weight = Decimal(weight)

        except (
            InvalidOperation,
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                "Please enter a valid parcel weight."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        # ----------------------------------------------------
        # Weight must be greater than zero.
        # ----------------------------------------------------

        if weight <= Decimal("0"):

            messages.error(
                request,
                "Parcel weight must be greater than 0."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        # ====================================================
        # DELIVERY CHARGE CALCULATION
        # ====================================================
        #
        # IMPORTANT:
        #
        # This uses parcels/utils.py.
        #
        # The rates are read from DeliveryChargeRate, which
        # means the administrator controls the actual charge.
        # ====================================================

        try:

            delivery_charge = calculate_delivery_charge(
                weight
            )

        except ValueError as error:

            messages.error(
                request,
                str(error)
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        # ====================================================
        # PARCEL TYPE VALIDATION
        # ====================================================

        valid_parcel_types = dict(
            Parcel.PARCEL_TYPE_CHOICES
        )

        if parcel_type not in valid_parcel_types:

            messages.error(
                request,
                "Invalid parcel type."
            )

            return render(
                request,
                "parcels/create_parcel.html",
                {
                    "rates": rates
                }
            )


        # ====================================================
        # CREATE PARCEL + PAYMENT + TRACKING
        # ====================================================

        try:

            with transaction.atomic():

                # ------------------------------------------------
                # Generate tracking number.
                # ------------------------------------------------

                tracking_number = (
                    generate_tracking_number()
                )

                # ------------------------------------------------
                # Create parcel.
                # ------------------------------------------------

                parcel = Parcel.objects.create(

                    customer=request.user,

                    tracking_number=tracking_number,

                    sender_name=sender_name,

                    sender_phone=sender_phone,

                    sender_address=sender_address,

                    receiver_name=receiver_name,

                    receiver_phone=receiver_phone,

                    receiver_address=receiver_address,

                    parcel_type=parcel_type,

                    weight=weight,

                    description=description,

                    pickup_date=pickup_date,

                    delivery_date=delivery_date,

                    # ------------------------------------------------
                    # Delivery charge is calculated on the server.
                    # ------------------------------------------------

                    delivery_charge=delivery_charge,

                    status="pending"

                )


                # ------------------------------------------------
                # CREATE PAYMENT
                # ------------------------------------------------
                #
                # The customer does not choose a payment method
                # during parcel creation.
                #
                # SHATHIMART automatically creates the payment as:
                #
                # Method = COD
                # Status = Pending
                # Amount = Delivery Charge
                # ------------------------------------------------

                Payment.objects.create(

                    parcel=parcel,

                    amount=delivery_charge,

                    payment_method="cod",

                    payment_status="pending"

                )


                # ------------------------------------------------
                # CREATE INITIAL TRACKING HISTORY
                # ------------------------------------------------

                create_tracking_history(

                    parcel=parcel,

                    status="pending",

                    location=sender_address,

                    remarks=(
                        "Parcel created successfully. "
                        f"Delivery charge: "
                        f"Rs. {delivery_charge:.2f}"
                    )

                )


        except Exception:

            messages.error(

                request,

                "Unable to create parcel. Please try again."

            )

            return render(

                request,

                "parcels/create_parcel.html",

                {
                    "rates": rates
                }

            )


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        messages.success(

            request,

            (
                "Parcel created successfully. "
                f"Tracking number: "
                f"{parcel.tracking_number}. "
                f"Delivery charge: "
                f"Rs. {delivery_charge:.2f}"
            )

        )


        # ----------------------------------------------------
        # Redirect to customer's parcel detail page.
        # ----------------------------------------------------

        return redirect(

            "parcel_detail",

            parcel_id=parcel.id

        )


    # ========================================================
    # GET REQUEST
    # ========================================================

    return render(

        request,

        "parcels/create_parcel.html",

        {
            "rates": rates
        }

    )


# ============================================================
# CUSTOMER PARCEL DETAIL
# ============================================================

@login_required
def parcel_detail(
    request,
    parcel_id
):
    """
    Display parcel details for the customer who owns it.
    """

    parcel = get_object_or_404(

        Parcel.objects.select_related(

            "payment",

            "delivery",

            "delivery__delivery_staff"

        ),

        id=parcel_id,

        customer=request.user

    )

    # --------------------------------------------------------
    # Get tracking history.
    # --------------------------------------------------------

    tracking_history = (

        parcel.tracking_history

        .all()

        .order_by("-created_at")

    )

    # --------------------------------------------------------
    # Get payment safely.
    # --------------------------------------------------------

    payment = getattr(

        parcel,

        "payment",

        None

    )

    return render(

        request,

        "parcels/parcel_detail.html",

        {
            "parcel": parcel,
            "tracking_history": tracking_history,
            "payment": payment,
        }

    )


# ============================================================
# PUBLIC TRACKING
# ============================================================

def track_parcel(request):
    """
    Allow anyone to track a parcel using its tracking number.
    """

    tracking_number = request.GET.get(
        "tracking_number",
        ""
    ).strip()

    parcel = None

    tracking_history = []

    error = None


    # ========================================================
    # SEARCH PARCEL
    # ========================================================

    if tracking_number:

        parcel = (

            Parcel.objects

            .filter(

                tracking_number__iexact=
                tracking_number

            )

            .select_related(

                "customer",

                "delivery",

                "delivery__delivery_staff",

                "payment"

            )

            .first()

        )


        # ----------------------------------------------------
        # Parcel found.
        # ----------------------------------------------------

        if parcel:

            tracking_history = (

                parcel.tracking_history

                .all()

                .order_by("-created_at")

            )


        # ----------------------------------------------------
        # Parcel not found.
        # ----------------------------------------------------

        else:

            error = (

                "No parcel was found with this "
                "tracking number."

            )


    return render(

        request,

        "parcels/track_parcel.html",

        {

            "parcel": parcel,

            "tracking_history":
                tracking_history,

            "error": error,

            "tracking_number":
                tracking_number,

        }

    )


# ============================================================
# TRACK BY NUMBER
# ============================================================

def track_parcel_by_number(
    request,
    tracking_number
):
    """
    Track a parcel directly from its tracking number URL.
    """

    parcel = (

        Parcel.objects

        .filter(

            tracking_number__iexact=

            tracking_number

        )

        .select_related(

            "customer",

            "delivery",

            "delivery__delivery_staff",

            "payment"

        )

        .first()

    )


    # --------------------------------------------------------
    # Parcel not found.
    # --------------------------------------------------------

    if not parcel:

        messages.error(

            request,

            "No parcel was found with that tracking number."

        )

        return redirect(

            "track_parcel"

        )


    # --------------------------------------------------------
    # Get tracking history.
    # --------------------------------------------------------

    tracking_history = (

        parcel.tracking_history

        .all()

        .order_by("-created_at")

    )


    return render(

        request,

        "parcels/track_parcel.html",

        {

            "parcel": parcel,

            "tracking_history":
                tracking_history,

            "tracking_number":
                parcel.tracking_number,

        }

    )


# ============================================================
# ADMIN ACCESS CHECK
# ============================================================

def is_admin(request):
    """
    Check whether the current user is an administrator.

    Superusers are always considered administrators.

    Normal users must have:

        request.user.profile.role == "admin"
    """

    # --------------------------------------------------------
    # User must be logged in.
    # --------------------------------------------------------

    if not request.user.is_authenticated:

        return False


    # --------------------------------------------------------
    # Django superuser.
    # --------------------------------------------------------

    if request.user.is_superuser:

        return True


    # --------------------------------------------------------
    # Get customer profile.
    # --------------------------------------------------------

    profile = getattr(

        request.user,

        "profile",

        None

    )


    if not profile:

        return False


    # --------------------------------------------------------
    # Check profile role.
    # --------------------------------------------------------

    return profile.role == "admin"


# ============================================================
# ADMIN PARCEL LIST
# ============================================================

@login_required
def admin_parcel_list(request):
    """
    Display all parcels to administrators.
    """

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    if not is_admin(request):

        messages.error(

            request,

            "You are not authorized to access parcel management."

        )

        return redirect("dashboard")


    # --------------------------------------------------------
    # Get all parcels.
    # --------------------------------------------------------

    parcels = (

        Parcel.objects

        .select_related(

            "customer",

            "delivery",

            "delivery__delivery_staff",

            "payment"

        )

        .order_by("-created_at")

    )


    return render(

        request,

        "parcels/admin_parcel_list.html",

        {

            "parcels": parcels

        }

    )


# ============================================================
# ADMIN PARCEL DETAIL
# ============================================================

@login_required
def admin_parcel_detail(
    request,
    parcel_id
):
    """
    Display complete parcel information for administrators.
    """

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    if not is_admin(request):

        messages.error(

            request,

            "You are not authorized to access this parcel."

        )

        return redirect("dashboard")


    # --------------------------------------------------------
    # Get parcel.
    # --------------------------------------------------------

    parcel = get_object_or_404(

        Parcel.objects.select_related(

            "customer",

            "delivery",

            "delivery__delivery_staff",

            "payment"

        ),

        id=parcel_id

    )


    # --------------------------------------------------------
    # Tracking history.
    # --------------------------------------------------------

    tracking_history = (

        parcel.tracking_history

        .all()

        .order_by("-created_at")

    )


    # --------------------------------------------------------
    # Payment.
    # --------------------------------------------------------

    payment = getattr(

        parcel,

        "payment",

        None

    )


    return render(

        request,

        "parcels/admin_parcel_detail.html",

        {

            "parcel": parcel,

            "tracking_history":
                tracking_history,

            "payment": payment,

        }

    )


# ============================================================
# ADMIN UPDATE DELIVERY CHARGE
# ============================================================

@login_required
def update_delivery_charge(
    request,
    parcel_id
):
    """
    Allow an administrator to manually update the delivery
    charge for a specific parcel.

    This is different from the general Delivery Charge Rates
    page.

    The Delivery Charge Rates page changes the default pricing
    rules for new parcel calculations.

    This function changes the final charge of one specific
    existing parcel.
    """

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    if not is_admin(request):

        messages.error(

            request,

            "You are not authorized to update delivery charges."

        )

        return redirect("dashboard")


    # --------------------------------------------------------
    # GET PARCEL
    # --------------------------------------------------------

    parcel = get_object_or_404(

        Parcel,

        id=parcel_id

    )


    # --------------------------------------------------------
    # ONLY POST REQUEST IS ALLOWED.
    # --------------------------------------------------------

    if request.method != "POST":

        return redirect(

            "admin_parcel_detail",

            parcel_id=parcel.id

        )


    # --------------------------------------------------------
    # GET CHARGE FROM FORM.
    # --------------------------------------------------------

    delivery_charge = request.POST.get(

        "delivery_charge",

        ""

    ).strip()


    # --------------------------------------------------------
    # REQUIRED FIELD CHECK.
    # --------------------------------------------------------

    if not delivery_charge:

        messages.error(

            request,

            "Please enter a delivery charge."

        )

        return redirect(

            "admin_parcel_detail",

            parcel_id=parcel.id

        )


    # --------------------------------------------------------
    # CONVERT TO DECIMAL.
    # --------------------------------------------------------

    try:

        delivery_charge = Decimal(

            delivery_charge

        )

    except (

        InvalidOperation,

        ValueError,

        TypeError

    ):

        messages.error(

            request,

            "Please enter a valid delivery charge."

        )

        return redirect(

            "admin_parcel_detail",

            parcel_id=parcel.id

        )


    # --------------------------------------------------------
    # NEGATIVE VALUE CHECK.
    # --------------------------------------------------------

    if delivery_charge < 0:

        messages.error(

            request,

            "Delivery charge cannot be negative."

        )

        return redirect(

            "admin_parcel_detail",

            parcel_id=parcel.id

        )


    # ========================================================
    # UPDATE PARCEL + PAYMENT
    # ========================================================

    with transaction.atomic():

        # ----------------------------------------------------
        # Update parcel delivery charge.
        # ----------------------------------------------------

        parcel.delivery_charge = delivery_charge

        parcel.save(

            update_fields=[

                "delivery_charge",

                "updated_at"

            ]

        )


        # ----------------------------------------------------
        # Get existing payment or create one.
        # ----------------------------------------------------

        payment, created = (

            Payment.objects.get_or_create(

                parcel=parcel,

                defaults={

                    "amount":
                        delivery_charge,

                    "payment_method":
                        "cod",

                    "payment_status":
                        "pending",

                }

            )

        )


        # ----------------------------------------------------
        # If payment already exists, update its amount.
        # ----------------------------------------------------

        if not created:

            payment.amount = delivery_charge

            payment.save(

                update_fields=[

                    "amount",

                    "updated_at"

                ]

            )


    # ========================================================
    # SUCCESS MESSAGE
    # ========================================================

    messages.success(

        request,

        (

            "Delivery charge updated successfully "
            f"to Rs. {delivery_charge:.2f}."

        )

    )


    return redirect(

        "admin_parcel_detail",

        parcel_id=parcel.id

    )


# ============================================================
# ADMIN UPDATE PARCEL STATUS
# ============================================================

@login_required
def update_parcel_status(
    request,
    parcel_id
):
    """
    Allow an administrator to update parcel status and create
    a tracking history record.
    """

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    if not is_admin(request):

        messages.error(

            request,

            "You are not authorized to update parcel status."

        )

        return redirect("dashboard")


    # --------------------------------------------------------
    # GET PARCEL.
    # --------------------------------------------------------

    parcel = get_object_or_404(

        Parcel,

        id=parcel_id

    )


    # ========================================================
    # POST REQUEST
    # ========================================================

    if request.method == "POST":

        new_status = request.POST.get(

            "status",

            ""

        ).strip()

        location = request.POST.get(

            "location",

            ""

        ).strip()

        remarks = request.POST.get(

            "remarks",

            ""

        ).strip()


        # ----------------------------------------------------
        # Validate status.
        # ----------------------------------------------------

        valid_statuses = dict(

            Parcel.STATUS_CHOICES

        )


        if new_status not in valid_statuses:

            messages.error(

                request,

                "Invalid parcel status."

            )

            return redirect(

                "admin_parcel_detail",

                parcel_id=parcel.id

            )


        # ----------------------------------------------------
        # Update parcel status.
        # ----------------------------------------------------

        parcel.status = new_status


        # ----------------------------------------------------
        # Automatically set delivery date when parcel is
        # marked as delivered.
        # ----------------------------------------------------

        if new_status == "delivered":

            if not parcel.delivery_date:

                parcel.delivery_date = (

                    timezone.localdate()

                )


        # ----------------------------------------------------
        # Save parcel.
        # ----------------------------------------------------

        parcel.save()


        # ----------------------------------------------------
        # Create tracking history.
        # ----------------------------------------------------

        create_tracking_history(

            parcel=parcel,

            status=new_status,

            location=location,

            remarks=remarks

        )


        # ----------------------------------------------------
        # Success message.
        # ----------------------------------------------------

        messages.success(

            request,

            "Parcel status updated successfully."

        )


    # ========================================================
    # REDIRECT
    # ========================================================

    return redirect(

        "admin_parcel_detail",

        parcel_id=parcel.id

    )


# ============================================================
# DELETE PARCEL
# ============================================================

@login_required
def delete_parcel(
    request,
    parcel_id
):
    """
    Delete a parcel.

    Only administrators can delete parcels.
    """

    # --------------------------------------------------------
    # ADMIN CHECK
    # --------------------------------------------------------

    if not is_admin(request):

        messages.error(

            request,

            "You are not authorized to delete parcels."

        )

        return redirect("dashboard")


    # --------------------------------------------------------
    # GET PARCEL.
    # --------------------------------------------------------

    parcel = get_object_or_404(

        Parcel,

        id=parcel_id

    )


    # ========================================================
    # DELETE ONLY WITH POST
    # ========================================================

    if request.method == "POST":

        tracking_number = (

            parcel.tracking_number

        )


        # ----------------------------------------------------
        # Delete parcel.
        #
        # Related TrackingHistory and Payment records will
        # also be deleted because their ForeignKeys use
        # on_delete=models.CASCADE.
        # ----------------------------------------------------

        parcel.delete()


        # ----------------------------------------------------
        # Success message.
        # ----------------------------------------------------

        messages.success(

            request,

            (

                f"Parcel {tracking_number} "
                f"was deleted successfully."

            )

        )


        return redirect(

            "admin_parcel_list"

        )


    # --------------------------------------------------------
    # If request is not POST, return to detail page.
    # --------------------------------------------------------

    return redirect(

        "admin_parcel_detail",

        parcel_id=parcel.id

    )

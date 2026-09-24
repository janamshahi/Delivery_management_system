from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .forms import RegisterForm, ProfileUpdateForm
from .models import CustomerProfile

from parcels.models import Parcel


# ============================================================
# HOME
# ============================================================

def home(request):
    return render(
        request,
        "home.html"
    )


# ============================================================
# ABOUT
# ============================================================

def about(request):
    """
    Public SHATHIMART About page.

    This page is available to both logged-in and
    logged-out users.
    """

    return render(
        request,
        "about.html"
    )


# ============================================================
# PUBLIC PARCEL TRACKING
# ============================================================

def track_parcel(request):
    """
    Public parcel tracking page.

    This page is available to both logged-in and logged-out users.
    It does not redirect customers to the dashboard.
    """

    tracking_number = request.GET.get(
        "tracking_number",
        ""
    ).strip()

    parcel = None
    searched = False

    if tracking_number:
        searched = True

        parcel = (
            Parcel.objects
            .filter(
                tracking_number__iexact=tracking_number
            )
            .select_related(
                "customer",
                "delivery"
            )
            .prefetch_related(
                "tracking_history"
            )
            .first()
        )

    context = {
        "parcel": parcel,
        "tracking_number": tracking_number,
        "searched": searched,
    }

    return render(
        request,
        "parcels/track_parcel.html",
        context
    )


# ============================================================
# CUSTOMER REGISTRATION
# ============================================================

def register_view(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect("admin_dashboard")

        profile, created = CustomerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role == "admin":
            return redirect("admin_dashboard")

        if profile.role == "delivery_staff":
            return redirect("staff_dashboard")

        return redirect("dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            CustomerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "role": "customer"
                }
            )

            messages.success(
                request,
                "Registration successful. You can now log in."
            )

            return redirect("login")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


# ============================================================
# CUSTOMER LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect("admin_dashboard")

        profile, created = CustomerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role == "admin":
            return redirect("admin_dashboard")

        if profile.role == "delivery_staff":
            return redirect("staff_dashboard")

        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

            return render(
                request,
                "accounts/login.html"
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:

            messages.error(
                request,
                "Invalid username or password."
            )

            return render(
                request,
                "accounts/login.html"
            )

        if not user.is_active:

            messages.error(
                request,
                "Your account is inactive."
            )

            return render(
                request,
                "accounts/login.html"
            )

        profile, created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role != "customer":

            messages.error(
                request,
                "Please use the correct login page for your account."
            )

            return render(
                request,
                "accounts/login.html"
            )

        login(
            request,
            user
        )

        messages.success(
            request,
            f"Welcome back, {user.username}!"
        )

        return redirect("dashboard")

    return render(
        request,
        "accounts/login.html"
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

def forgot_password(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect("admin_dashboard")

        profile, created = CustomerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role == "admin":
            return redirect("admin_dashboard")

        if profile.role == "delivery_staff":
            return redirect("staff_dashboard")

        return redirect("dashboard")

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip()

        new_password = request.POST.get(
            "new_password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if (
            not email
            or not new_password
            or not confirm_password
        ):

            messages.error(
                request,
                "Please fill in all fields."
            )

            return render(
                request,
                "accounts/forgot_password.html"
            )

        if len(new_password) < 8:

            messages.error(
                request,
                "Password must be at least 8 characters long."
            )

            return render(
                request,
                "accounts/forgot_password.html"
            )

        if new_password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "accounts/forgot_password.html"
            )

        try:

            user = User.objects.get(
                email__iexact=email
            )

        except User.DoesNotExist:

            messages.error(
                request,
                "No account was found with this email address."
            )

            return render(
                request,
                "accounts/forgot_password.html"
            )

        if not user.is_active:

            messages.error(
                request,
                "Your account is inactive."
            )

            return render(
                request,
                "accounts/forgot_password.html"
            )

        profile, created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role != "customer":

            messages.error(
                request,
                "Password reset is only available for customer accounts."
            )

            return render(
                request,
                "accounts/forgot_password.html"
            )

        user.set_password(
            new_password
        )

        user.save()

        messages.success(
            request,
            "Password changed successfully. You can now log in."
        )

        return redirect("login")

    return render(
        request,
        "accounts/forgot_password.html"
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login_view(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:

            profile, created = CustomerProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    "role": "admin"
                }
            )

            if profile.role != "admin":

                profile.role = "admin"

                profile.save(
                    update_fields=["role"]
                )

            return redirect(
                "admin_dashboard"
            )

        profile, created = CustomerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role == "admin":

            return redirect(
                "admin_dashboard"
            )

        messages.info(
            request,
            "This account does not have administrator access."
        )

        logout(request)

        return redirect(
            "admin_login"
        )

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

            return render(
                request,
                "accounts/admin_login.html"
            )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:

            messages.error(
                request,
                "Invalid username or password."
            )

            return render(
                request,
                "accounts/admin_login.html"
            )

        if not user.is_active:

            messages.error(
                request,
                "Your account is inactive."
            )

            return render(
                request,
                "accounts/admin_login.html"
            )

        if user.is_superuser:

            profile, created = CustomerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "role": "admin"
                }
            )

            if profile.role != "admin":

                profile.role = "admin"

                profile.save(
                    update_fields=["role"]
                )

            login(
                request,
                user
            )

            messages.success(
                request,
                "Welcome to the administrator dashboard."
            )

            return redirect(
                "admin_dashboard"
            )

        profile, created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "role": "customer"
            }
        )

        if profile.role != "admin":

            messages.error(
                request,
                "You do not have administrator access."
            )

            return render(
                request,
                "accounts/admin_login.html"
            )

        login(
            request,
            user
        )

        messages.success(
            request,
            "Welcome to the administrator dashboard."
        )

        return redirect(
            "admin_dashboard"
        )

    return render(
        request,
        "accounts/admin_login.html"
    )


# ============================================================
# DELIVERY STAFF LOGIN
# ============================================================

def staff_login_view(request):

    # ========================================================
    # ALREADY LOGGED-IN USER
    # ========================================================

    if request.user.is_authenticated:

        # ----------------------------------------------------
        # SUPERUSER
        # ----------------------------------------------------

        if request.user.is_superuser:

            messages.info(
                request,
                "Administrator accounts cannot use the staff login."
            )

            return redirect(
                "admin_dashboard"
            )

        # ----------------------------------------------------
        # SAFELY GET CUSTOMER PROFILE
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # Do not use:
        #
        #     request.user.customer_profile
        #
        # because the profile may not exist.
        #
        # ----------------------------------------------------

        profile, created = CustomerProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "role": "customer"
            }
        )

        # ----------------------------------------------------
        # DELIVERY STAFF
        # ----------------------------------------------------

        if profile.role == "delivery_staff":

            return redirect(
                "staff_dashboard"
            )

        # ----------------------------------------------------
        # ADMIN
        # ----------------------------------------------------

        if profile.role == "admin":

            messages.info(
                request,
                "Please use the administrator login."
            )

            return redirect(
                "admin_dashboard"
            )

        # ----------------------------------------------------
        # CUSTOMER / OTHER ROLE
        # ----------------------------------------------------

        messages.info(
            request,
            "This account does not have delivery staff access."
        )

        logout(request)

        return redirect(
            "staff_login"
        )

    # ========================================================
    # STAFF LOGIN FORM
    # ========================================================

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # VALIDATE INPUT
        # ----------------------------------------------------

        if not username or not password:

            messages.error(
                request,
                "Please enter username and password."
            )

            return render(
                request,
                "accounts/staff_login.html"
            )

        # ----------------------------------------------------
        # AUTHENTICATE
        # ----------------------------------------------------

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # ----------------------------------------------------
        # INVALID LOGIN
        # ----------------------------------------------------

        if user is None:

            messages.error(
                request,
                "Invalid username or password."
            )

            return render(
                request,
                "accounts/staff_login.html"
            )

        # ----------------------------------------------------
        # INACTIVE USER
        # ----------------------------------------------------

        if not user.is_active:

            messages.error(
                request,
                "Your account is inactive."
            )

            return render(
                request,
                "accounts/staff_login.html"
            )

        # ----------------------------------------------------
        # SUPERUSER
        # ----------------------------------------------------

        if user.is_superuser:

            messages.error(
                request,
                "Administrator accounts cannot use the staff login."
            )

            return render(
                request,
                "accounts/staff_login.html"
            )

        # ----------------------------------------------------
        # SAFELY GET OR CREATE CUSTOMER PROFILE
        # ----------------------------------------------------
        #
        # This is the important fix.
        #
        # The old code was:
        #
        #     profile = user.customer_profile
        #
        # If the CustomerProfile did not exist, Django raised:
        #
        #     AttributeError:
        #     'User' object has no attribute 'customer_profile'
        #
        # get_or_create() prevents that error.
        #
        # ----------------------------------------------------

        profile, created = CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "role": "customer"
            }
        )

        # ----------------------------------------------------
        # CHECK STAFF ROLE
        # ----------------------------------------------------

        if profile.role != "delivery_staff":

            messages.error(
                request,
                "This account is not registered as delivery staff."
            )

            return render(
                request,
                "accounts/staff_login.html"
            )

        # ----------------------------------------------------
        # LOGIN STAFF
        # ----------------------------------------------------

        login(
            request,
            user
        )

        messages.success(
            request,
            f"Welcome, {user.username}!"
        )

        return redirect(
            "staff_dashboard"
        )

    # ========================================================
    # GET - STAFF LOGIN PAGE
    # ========================================================

    return render(
        request,
        "accounts/staff_login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect(
        "home"
    )


# ============================================================
# CUSTOMER DASHBOARD
# ============================================================

@login_required
def dashboard(request):

    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "customer"
        }
    )

    if request.user.is_superuser:

        if profile.role != "admin":

            profile.role = "admin"

            profile.save(
                update_fields=["role"]
            )

        return redirect(
            "admin_dashboard"
        )

    if profile.role == "admin":

        return redirect(
            "admin_dashboard"
        )

    if profile.role == "delivery_staff":

        return redirect(
            "staff_dashboard"
        )

    parcels = (
        Parcel.objects
        .filter(
            customer=request.user
        )
        .order_by(
            "-created_at"
        )
    )

    recent_parcels = parcels[:5]

    total_parcels = parcels.count()

    pending_count = parcels.filter(
        status__in=[
            "pending",
            "pickup_requested"
        ]
    ).count()

    in_transit_count = parcels.filter(
        status__in=[
            "assigned",
            "picked_up",
            "in_transit"
        ]
    ).count()

    out_for_delivery_count = parcels.filter(
        status="out_for_delivery"
    ).count()

    delivered_count = parcels.filter(
        status="delivered"
    ).count()

    context = {
        "profile": profile,
        "parcels": parcels,
        "recent_parcels": recent_parcels,
        "total_parcels": total_parcels,
        "pending_count": pending_count,
        "in_transit_count": in_transit_count,
        "out_for_delivery_count": out_for_delivery_count,
        "delivered_count": delivered_count,
    }

    return render(
        request,
        "dashboard/customer_dashboard.html",
        context
    )


# ============================================================
# CUSTOMER PROFILE
# ============================================================

@login_required
def profile_view(request):

    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "customer"
        }
    )

    if request.user.is_superuser:

        if profile.role != "admin":

            profile.role = "admin"

            profile.save(
                update_fields=["role"]
            )

    parcels = (
        Parcel.objects
        .filter(
            customer=request.user
        )
        .order_by(
            "-created_at"
        )
    )

    total_parcels = parcels.count()

    delivered_count = parcels.filter(
        status="delivered"
    ).count()

    cancelled_count = parcels.filter(
        status="cancelled"
    ).count()

    active_count = parcels.filter(
        status__in=[
            "pending",
            "pickup_requested",
            "assigned",
            "picked_up",
            "in_transit",
            "out_for_delivery",
            "rescheduled",
        ]
    ).count()

    recent_parcels = parcels[:5]

    context = {
        "profile": profile,
        "parcels": parcels,
        "total_parcels": total_parcels,
        "delivered_count": delivered_count,
        "cancelled_count": cancelled_count,
        "active_count": active_count,
        "recent_parcels": recent_parcels,
    }

    return render(
        request,
        "accounts/profile.html",
        context
    )


# ============================================================
# EDIT CUSTOMER PROFILE
# ============================================================

@login_required
def edit_profile(request):

    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "customer"
        }
    )

    if request.user.is_superuser:

        if profile.role != "admin":

            profile.role = "admin"

            profile.save(
                update_fields=["role"]
            )

    if request.method == "POST":

        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect(
                "profile"
            )

    else:

        form = ProfileUpdateForm(
            instance=profile
        )

    context = {
        "form": form,
        "profile": profile,
    }

    return render(
        request,
        "accounts/edit_profile.html",
        context
    )


# ============================================================
# CUSTOMER PARCELS
# ============================================================

@login_required
def my_parcels(request):

    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "role": "customer"
        }
    )

    if request.user.is_superuser:

        return redirect(
            "admin_dashboard"
        )

    if profile.role == "admin":

        return redirect(
            "admin_dashboard"
        )

    if profile.role == "delivery_staff":

        return redirect(
            "staff_dashboard"
        )

    parcels = (
        Parcel.objects
        .filter(
            customer=request.user
        )
        .select_related(
            "delivery",
            "delivery__delivery_staff"
        )
        .order_by(
            "-created_at"
        )
    )

    total_count = parcels.count()

    pending_count = parcels.filter(
        status__in=[
            "pending",
            "pickup_requested"
        ]
    ).count()

    active_count = parcels.filter(
        status__in=[
            "assigned",
            "picked_up",
            "in_transit",
            "out_for_delivery",
            "rescheduled"
        ]
    ).count()

    delivered_count = parcels.filter(
        status="delivered"
    ).count()

    cancelled_count = parcels.filter(
        status="cancelled"
    ).count()

    context = {
        "profile": profile,
        "parcels": parcels,
        "total_count": total_count,
        "pending_count": pending_count,
        "active_count": active_count,
        "delivered_count": delivered_count,
        "cancelled_count": cancelled_count,
    }

    return render(
        request,
        "parcels/my_parcels.html",
        context
    )

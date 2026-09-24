from django.urls import path

from . import views

urlpatterns = [


# ========================================================
# ADMIN DASHBOARD
# ========================================================

path(
    "admin/",
    views.admin_dashboard,
    name="admin_dashboard"
),


# ========================================================
# ADMIN PARCEL MANAGEMENT
# ========================================================

path(
    "admin/parcels/",
    views.parcel_management,
    name="admin_parcel_list"
),


# ========================================================
# ADMIN TRACKING MANAGEMENT
# ========================================================

path(
    "admin/tracking/",
    views.tracking_management,
    name="admin_tracking"
),


# ========================================================
# ADMIN - SINGLE PARCEL TRACKING
#
# Example:
# /dashboard/admin/tracking/15/
#
# This page shows tracking history of ONLY
# the selected parcel.
# ========================================================

path(
    "admin/tracking/<int:parcel_id>/",
    views.parcel_tracking,
    name="parcel_tracking"
),


# ========================================================
# ADMIN DELIVERY MANAGEMENT
# ========================================================

path(
    "admin/deliveries/",
    views.delivery_management,
    name="admin_deliveries"
),


# ========================================================
# ASSIGN DELIVERY STAFF
# ========================================================

path(
    "admin/deliveries/<int:parcel_id>/assign/",
    views.assign_delivery_staff,
    name="assign_delivery_staff"
),


# ========================================================
# ADMIN DELIVERY CHARGE MANAGEMENT
#
# Admin can configure:
# - Up to 1 KG
# - Up to 3 KG
# - Up to 5 KG
# - Above 5 KG
#
# Example:
# /dashboard/admin/delivery-charges/
# ========================================================

path(
    "admin/delivery-charges/",
    views.delivery_charge_management,
    name="delivery_charge_management"
),


# ========================================================
# ADMIN CUSTOMER MANAGEMENT
# ========================================================

path(
    "admin/customers/",
    views.customer_management,
    name="admin_customers"
),


# ========================================================
# ADMIN STAFF MANAGEMENT
# ========================================================

path(
    "admin/staff/",
    views.staff_management,
    name="admin_staff"
),


# ========================================================
# ADMINISTRATOR MANAGEMENT
# ========================================================

path(
    "admin/administrators/",
    views.administrator_management,
    name="admin_administrators"
),


# ========================================================
# ADMINISTRATOR PROFILE
# ========================================================

path(
    "admin/administrators/<int:user_id>/",
    views.administrator_profile,
    name="administrator_profile"
),


# ========================================================
# ADMIN REPORTS
# ========================================================

path(
    "admin/reports/",
    views.reports,
    name="admin_reports"
),


# ========================================================
# DELIVERY STAFF DASHBOARD
# ========================================================

path(
    "staff/",
    views.staff_dashboard,
    name="staff_dashboard"
),


# ========================================================
# DELIVERY STAFF DASHBOARD ALIAS
#
# URL:
# /dashboard/staffdashboard/
# ========================================================

path(
    "staffdashboard/",
    views.staff_dashboard,
    name="staff_dashboard_page"
),


# ========================================================
# DELIVERY STAFF PROFILE
# ========================================================

path(
    "staff/profile/",
    views.staff_profile,
    name="staff_profile"
),


# ========================================================
# DELIVERY STAFF - MY PARCELS
# ========================================================

path(
    "staff/parcels/",
    views.staff_parcels,
    name="staff_parcels"
),


# ========================================================
# DELIVERY STAFF - PARCEL DETAIL / UPDATE
# ========================================================

path(
    "staff/parcels/<int:parcel_id>/",
    views.staff_parcel_detail,
    name="staff_parcel_detail"
),


]
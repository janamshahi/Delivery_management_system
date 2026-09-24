from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # CUSTOMER
    # ========================================================

    path(
        "",
        views.parcel_list,
        name="parcel_list"
    ),

    path(
        "create/",
        views.create_parcel,
        name="create_parcel"
    ),

    path(
        "<int:parcel_id>/",
        views.parcel_detail,
        name="parcel_detail"
    ),


    # ========================================================
    # TRACKING
    # ========================================================

    path(
        "track/",
        views.track_parcel,
        name="track_parcel"
    ),

    path(
        "track/<str:tracking_number>/",
        views.track_parcel_by_number,
        name="track_parcel_by_number"
    ),


    # ========================================================
    # ADMIN
    # ========================================================

    path(
        "admin/",
        views.admin_parcel_list,
        name="admin_parcel_list"
    ),

    path(
        "admin/<int:parcel_id>/",
        views.admin_parcel_detail,
        name="admin_parcel_detail"
    ),

    path(
        "admin/<int:parcel_id>/status/",
        views.update_parcel_status,
        name="update_parcel_status"
    ),

    path(
        "admin/<int:parcel_id>/delivery-charge/",
        views.update_delivery_charge,
        name="update_delivery_charge"
    ),

    path(
        "admin/<int:parcel_id>/delete/",
        views.delete_parcel,
        name="delete_parcel"
    ),

]
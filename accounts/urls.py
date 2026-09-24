from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),

    # Public parcel tracking
    path("track/", views.track_parcel, name="track_parcel"),

    # Customer authentication
    path("login/", views.login_view, name="login"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("register/", views.register_view, name="register"),

    # Admin authentication
    path("admin-login/", views.admin_login_view, name="admin_login"),

    # Delivery staff authentication
    path("staff-login/", views.staff_login_view, name="staff_login"),

    # Logout
    path("logout/", views.logout_view, name="logout"),

    # Customer dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Customer profile
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="profile_edit"),

    # Customer parcels
    path("parcels/", views.my_parcels, name="my_parcels"),
    
    path("about/", views.about, name="about"),
]

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required(login_url="login")
def notification_list(request):

    notifications = Notification.objects.filter(
        user=request.user
    ).select_related(
        "parcel"
    )

    context = {

        "notifications": notifications,

    }

    return render(
        request,
        "notifications/notification_list.html",
        context
    )


@login_required(login_url="login")
def mark_notification_read(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    if notification.parcel:

        return redirect(
            f"/track/?tracking_number={notification.parcel.tracking_number}"
        )

    return redirect("notification_list")


@login_required(login_url="login")
def mark_all_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    return redirect("notification_list")
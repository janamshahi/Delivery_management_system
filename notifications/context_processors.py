from .models import Notification


def notification_context(request):

    if not request.user.is_authenticated:

        return {
            "navbar_notifications": [],
            "unread_notifications_count": 0,
        }


    notifications = Notification.objects.filter(
        user=request.user
    ).select_related(
        "parcel"
    )[:8]


    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()


    return {

        "navbar_notifications": notifications,

        "unread_notifications_count": unread_count,

    }
from django.urls import path

from .views import instagram_webhook


urlpatterns = [
    path(
        "instagram/",
        instagram_webhook,
        name="instagram-webhook",
    ),
]
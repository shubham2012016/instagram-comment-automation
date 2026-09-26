from django.urls import path
from .views import instagram_webhook, instagram_connect, instagram_callback

urlpatterns = [
    path("instagram/", instagram_webhook, name="instagram-webhook"),
    path("instagram/connect/", instagram_connect, name="instagram-connect"),
    path("instagram/callback/", instagram_callback, name="instagram-callback"),
]

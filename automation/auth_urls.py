from django.urls import path
from .views import instagram_connect, instagram_callback

urlpatterns = [
    path("instagram/", instagram_connect, name="instagram-connect"),
    path("instagram/callback/", instagram_callback, name="instagram-callback"),
]

"""URL routes. Feature apps add theirs in later stories."""

from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("", include("web.urls")),
]

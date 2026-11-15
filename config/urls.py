"""URL routes. Feature apps add theirs in later stories."""

from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("", include("web.urls")),
]

# P12 «Fant ikke siden», in the shell for a signed-in Student (Conventions: Templates).
handler404 = "web.views.not_found"

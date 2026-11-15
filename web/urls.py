from django.urls import path

from web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("courses/<int:course_id>/", views.course, name="course"),
    path("theme/", views.theme, name="theme"),
]

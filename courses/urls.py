from django.urls import path

from courses import views

app_name = "courses"

urlpatterns = [
    path("new/", views.create, name="create"),
    path("<int:course_id>/rename/", views.rename, name="rename"),
    path("<int:course_id>/delete/", views.delete, name="delete"),
]

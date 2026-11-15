from django.urls import path

from courses import views

app_name = "courses"

# Mounted at the site root: fag dialogs under /courses/, tema under /topics/, kilde under /sources/.
urlpatterns = [
    path("courses/new/", views.create, name="create"),
    path("courses/<int:course_id>/rename/", views.rename, name="rename"),
    path("courses/<int:course_id>/delete/", views.delete, name="delete"),
    path("courses/<int:course_id>/topics/new/", views.create_topic, name="create_topic"),
    path("topics/<int:topic_id>/rename/", views.rename_topic, name="rename_topic"),
    path("topics/<int:topic_id>/delete/", views.delete_topic, name="delete_topic"),
    path("sources/<int:source_id>/rename/", views.rename_source, name="rename_source"),
    path("sources/<int:source_id>/delete/", views.delete_source, name="delete_source"),
]

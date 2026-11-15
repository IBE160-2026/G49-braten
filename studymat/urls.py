from django.urls import path

from studymat import views

app_name = "studymat"

# Mounted at the site root, under the Topic the Source is added to.
urlpatterns = [
    path("topics/<int:topic_id>/sources/new/", views.add_source, name="add_source"),
]

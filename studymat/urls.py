from django.urls import path

from studymat import views

app_name = "studymat"

# Mounted at the site root, under the Topic the Source is added to.
urlpatterns = [
    path("privacy/", views.privacy, name="privacy"),
    path("topics/<int:topic_id>/sources/new/", views.add_source, name="add_source"),
    path("sources/<int:source_id>/generate/", views.generate, name="generate"),
    path("items/<str:kind>/<int:item_id>/delete/", views.delete_item, name="delete_item"),
]

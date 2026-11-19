from django.urls import path

from review import views

app_name = "review"

# Mounted at the site root, like quiz.
urlpatterns = [
    path("reviews/start/", views.start, name="start"),
    path("reviews/<int:review_id>/", views.session, name="session"),
    path("reviews/<int:review_id>/rate/", views.rate, name="rate"),
    # P08 «Bla i kort» (FR-14).
    path("topics/<int:topic_id>/cards/", views.browse_start, name="browse_start"),
    path("topics/<int:topic_id>/cards/<int:position>/", views.browse, name="browse"),
]

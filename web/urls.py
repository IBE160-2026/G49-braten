from django.urls import path

from web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("courses/<int:course_id>/", views.course, name="course"),
    path("courses/<int:course_id>/weak-quiz/", views.weak_quiz, name="weak_quiz"),
    path("topics/<int:topic_id>/", views.topic, name="topic"),
    path("theme/", views.theme, name="theme"),
]

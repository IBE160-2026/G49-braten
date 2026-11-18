from django.urls import path

from quiz import views

app_name = "quiz"

# Mounted at the site root: D06 under the Topic it starts from, P06 under /quizzes/.
urlpatterns = [
    path("topics/<int:topic_id>/quiz/new/", views.start, name="start"),
    path("quizzes/<int:quiz_id>/", views.resume, name="resume"),
    path("quizzes/<int:quiz_id>/<int:position>/", views.question, name="question"),
    path("quizzes/<int:quiz_id>/<int:position>/answer/", views.answer, name="answer"),
    path("quizzes/<int:quiz_id>/<int:position>/regrade/", views.regrade, name="regrade"),
]

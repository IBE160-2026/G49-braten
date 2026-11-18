from django.urls import path

from quiz import views

app_name = "quiz"

# Mounted at the site root: D06 under the Topic it starts from, P06 and P07 under /quizzes/.
urlpatterns = [
    path("topics/<int:topic_id>/quiz/new/", views.start, name="start"),
    path("quizzes/<int:quiz_id>/", views.resume, name="resume"),
    path("quizzes/<int:quiz_id>/result/", views.result, name="result"),
    path("quizzes/<int:quiz_id>/retry/", views.retry, name="retry"),
    path("quizzes/<int:quiz_id>/<int:position>/", views.question, name="question"),
    path("quizzes/<int:quiz_id>/<int:position>/answer/", views.answer, name="answer"),
    path("quizzes/<int:quiz_id>/<int:position>/regrade/", views.regrade, name="regrade"),
    path("quizzes/<int:quiz_id>/<int:position>/override/", views.override, name="override"),
]

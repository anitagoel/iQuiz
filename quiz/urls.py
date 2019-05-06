from django.urls import path
from django.http import HttpResponse
from . import views

urlpatterns = [
        # URL for launching LTI or showing homepage
        path('', views.launch.index, name='index'),

        # URL for manager/instructor
        path('quiz-settings', views.manager.edit_quiz_settings, name='edit_quiz_settings'),
        path('edit', views.manager.edit, name='edit'),
        path('home', views.manager.home, name='home'),
        path('grades', views.manager.grades, name='grades'),
        path('edit_question', views.manager.edit_question, name='edit_question'),
        path('add_question', views.manager.add_question, name="add_question"),
        path('publish', views.manager.publish, name="publish"),

        # URL for students
        path('student', views.student.home, name="student_home"),
        path('quiz', views.student.show_quiz, name="quiz"),
        path('quiz/save_response', views.student.save_response, name="save_response"),
        path('attempt_details', views.student.attempt_details, name="attempt_details"),
        path('attempt_analytics', views.student.attempt_analytics, name="attempt_analytics"),
        path('analytics_page', views.student.analytics_page, name="analytics_page"),
        ]
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
        # URL for launching LTI or showing homepage
        path('', views.launch.index, name='index'),

        # URL for manager/instructor
        path('quiz-settings', views.manager.edit_quiz_settings, name='edit_quiz_settings'),
        path('edit', views.manager.edit, name='edit'),
        path('home', views.manager.home, name='home'),
        path('grades', views.manager.grades, name='grades'),
        path('download/grade/excel', views.download_data.download_grade_data),
        path('download/report/excel/<int:attempt_id>', views.download_data.download_report_data),
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

        path('questionattemptstart', views.student.questionVisitTime, name="question_visit_time"),
        ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
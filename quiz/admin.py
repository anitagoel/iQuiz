from django.contrib import admin
from .models import Quiz, Question, QuizSettings
from .models.answer import Answer
from .models.lti_user import LTIUser
from .models.response import Response
from django.contrib.admin.models import LogEntry
admin.site.register(LogEntry)

# Register your models here.
admin.site.register(Quiz)
admin.site.register(QuizSettings)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(LTIUser)
admin.site.register(Response)
from django.forms import *
from pagedown.widgets import PagedownWidget
from ..models import QuizSettings


class QuizSettingsForm(ModelForm):
    information = CharField(widget=PagedownWidget(), strip=False, required=False)
    deadline = DateField(widget = DateInput(attrs={'placeholder': 'YYYY-MM-DD [HH:MM:SS]',}), required = False)

    class Meta:
        model = QuizSettings
        fields = ['randomizeQuestionOrder','deadline', 'duration', 'timeBetweenAttempt', 'maxAttempts' , 'information']
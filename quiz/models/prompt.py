from django import forms
from django.db import models
from pagedown.widgets import PagedownWidget
from . import *

class Prompt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.TextField()
    occur_before_question = models.IntegerField(help_text="Enter the question number before which the prompt will appear!")


class PromptResponse(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    prompt_response = models.TextField()
    events = models.JSONField()


class PromptForm(forms.ModelForm):
    question = forms.CharField(widget=PagedownWidget(attrs={'placeholder': 'Prompt Question Statement', 'rows': 2}),
                                      strip=False)

    class Meta:
        model = Prompt
        fields = ['question', 'occur_before_question']
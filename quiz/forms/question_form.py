from django import forms
from ..models import Question
from pagedown.widgets import PagedownWidget

class QuestionForm(forms.ModelForm):
	'''
	QuestionForm can be used by any type of Question to include the draft_statement and group number 
	as the fields in the form. The other fields for options are to be added by the question type itself.
	'''
	draft_statement = forms.CharField(widget=PagedownWidget())
	class Meta:
		model = Question
		fields = ["draft_statement"]
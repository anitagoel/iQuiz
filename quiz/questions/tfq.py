from django import forms
from django.shortcuts import render
from ..models import Question

from django.template import loader
from pagedown.widgets import PagedownWidget

from .question import AbstractQuestion
import markdown_deux


class TFQForm(forms.ModelForm):
    draft_statement = forms.CharField(
        widget=PagedownWidget(
            attrs=
            {'placeholder': 'Question Statement', 'rows': 2}
        ), strip=False)

    class Meta:
        model = Question
        fields = ['question_weight', 'draft_statement']


class TFQ(AbstractQuestion):
    """
    The class is to implement the Multiple Choice type Question.
    """
    CLASS_NAME = "TFQ"
    CLASS_VERBOSE_NAME = "True/False Question"
    # POST Request Variable name as used in TFQ template
    DRAFT_OPTIONS = "draft_options"
    DRAFT_STATEMENT = "draft_statement"
    CORRECT_RESPONSE = "correct_option"

    top_h3 = "Choose whether the following statement is True or False." #stores the header for TFQs
    options = [('true', 'True'), ('false', 'False')]

    @staticmethod
    def get_edit_view(request, question):
        """
        The function returns the Manager view of the TFQ as a view.
        """
        question.question_type = TFQ.CLASS_NAME
        message = "Please make sure form is valid!"
        correct_option_id = 'true'  # choose true by default

        if request.method == "POST":
            form = TFQForm(request.POST, instance=question)
            if TFQ.CORRECT_RESPONSE not in request.POST:
                message = "Please select the correct response!"
                return render(
                    request,
                    'questions/tfq-form.html',
                    dict(form=form, success=False, message=message,
                         correct_option_id=correct_option_id, top_h3=TFQ.top_h3)
                )
            else:
                correct_option_id = request.POST[TFQ.CORRECT_RESPONSE]
            if form.is_valid():
                qs = form.save(commit=False)
                qs.draft_expected_response = correct_option_id
                qs.save()
                message = "The question is saved/updated successfully!"
                return HttpResponseRedirect(reverse('edit'))

        else:
            form = TFQForm(instance=question)
        return render(
            request,
            'questions/tfq-form.html',
            dict(form=form, success=False, message=message,
                 correct_option_id=correct_option_id, top_h3=TFQ.top_h3)
        )

    @staticmethod
    def get_statement_html(question):
        if question.statement:
            html = markdown_deux.markdown(question.statement, 'default')
        else:
            html = ''
        return html

    @staticmethod
    def get_draft_statement_html(question):
        if question.draft_statement:
            html = markdown_deux.markdown(question.draft_statement, 'default')
        else:
            html = ''
        return html
    
    @staticmethod
    def get_student_view_html(question):
        template = loader.get_template('questions/tfq.html')
        context = dict(qid=question.id, statement=TFQ.get_statement_html(question), options=TFQ.options, top_h3=TFQ.top_h3)
        return template.render(context)

    @staticmethod
    def get_student_responded_view_html(question, response):
        template = loader.get_template('questions/tfq.html')
        context = dict(qid=question.id, statement=TFQ.get_statement_html(question), options=TFQ.options,
                       checked_option_id=response, top_h3=TFQ.top_h3)
        return template.render(context)


    @staticmethod
    def get_student_responded_paper_view_html(question, response):
        """
        Returns the HTML representation for the Question for the Responded Paper.
        It has disabled options, it can be used to generate the report of the student
        response.
        :param question:
        :param response: response corresponding to the question
        :return: string : html
        """
        correct_option_id = question.expected_response
        template = loader.get_template('questions/mcq.html')
        context = {
            'qid': question.id,
            'statement': TFQ.get_statement_html(question),
            'options': TFQ.options,
            'checked_option_id': response,
            'correct_option_id': correct_option_id
        }
        return template.render(context)


    @staticmethod
    def get_marks(question, response):
        weight = question.question_weight
        expected_response = question.expected_response
        if response == expected_response:
            return weight
        return 0
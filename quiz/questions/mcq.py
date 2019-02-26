import json

import markdown_deux
from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from django.template import loader
from pagedown.widgets import PagedownWidget


from quiz.utils import lti_utils as lti
from ..models import Question


class MCQForm(forms.ModelForm):
    draft_statement = forms.CharField(widget=PagedownWidget(attrs={'placeholder': 'Question Statement', 'rows': 2}),
                                      strip=False)

    class Meta:
        model = Question
        fields = ['question_weight', 'draft_statement']


class MCQ:
    """
    The class is to implement the Multiple Choice type Question.
    """
    CLASS_NAME = "MCQ"
    CLASS_VERBOSE_NAME = "Multiple Choice Question"
    # POST Request Variable name as used in MCQ template
    DRAFT_OPTIONS = "draft_options"
    DRAFT_STATEMENT = "draft_statement"
    CORRECT_RESPONSE = "correct_option"

    @staticmethod
    def get_edit_view(request, question):
        """
        The function returns the Manager view of the MCQ as a view.
        On success return to HttpResponseRedirect(reverse('edit')). 
        """
        question.question_type = MCQ.CLASS_NAME
        template = 'questions/mcq-form.html'
        message = None
        # Validate that manager is viewing this page
        if question.draft_options_data and question.draft_options_data != '':
            options = json.loads(question.draft_options_data)
            expected_option_id = question.draft_expected_response
        else:
            options = [['option_1', ''], ['option_2', '']]
            expected_option_id = []

        if request.method == "POST":
            form = MCQForm(request.POST, instance=question)
            options_list = request.POST.getlist(MCQ.DRAFT_OPTIONS)

            if MCQ.DRAFT_OPTIONS not in request.POST or len(options_list) < 2:
                message = "Add at least two options!"
                return render(request, template,
                              {'form': form, 'success': False, 'message': message, 'options': options,
                               'expected_option_id': expected_option_id})

            if MCQ.CORRECT_RESPONSE not in request.POST:
                message = "Please select the correct response!"
                return render(request, template,
                              {'form': form, 'success': False, 'message': message, 'options': options,
                               'expected_option_id': expected_option_id})
            else:
                expected_option_id = request.POST[MCQ.CORRECT_RESPONSE]

            option_tuples = []  # Store the option as tuples of the form (option_id, option_markdown)
            for i in range(len(options_list)):
                option = options_list[i]
                option_tuples.append(("option_" + str(i + 1), option))

            if form.is_valid():
                qs = form.save(commit=False)
                qs.draft_expected_response = expected_option_id
                qs.draft_options_data = json.dumps(option_tuples)
                qs.save()
                message = "The question is saved/updated successfully!"
                return HttpResponseRedirect(reverse('edit'))

        else:
            form = MCQForm(instance=question)
        return render(request, template, {'form': form, 'success': False, 'message': message, 'options': options,
                                                 'expected_option_id': expected_option_id})

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
        options = json.loads(question.options_data)
        template = loader.get_template('questions/mcq.html')
        context = {
            'qid': question.id,
            'statement': MCQ.get_statement_html(question),
            'options': options,
        }
        return template.render(context)

    @staticmethod
    def get_student_responded_view_html(question, response):
        options = json.loads(question.options_data)
        template = loader.get_template('questions/mcq.html')
        context = {
            'qid': question.id,
            'statement': MCQ.get_statement_html(question),
            'options': options,
            'checked_option_id': response,
        }
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
        options = json.loads(question.options_data)
        correct_option_id = question.expected_response
        template = loader.get_template('questions/mcq.html')
        context = {
            'qid': question.id,
            'statement': MCQ.get_statement_html(question),
            'options': options,
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

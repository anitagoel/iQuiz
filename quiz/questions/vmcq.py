import json

import markdown_deux
from django import forms
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse

from django.template import loader
from pagedown.widgets import PagedownWidget

from quiz.utils import lti_utils as lti
from ..models import Question
from .question import AbstractQuestion

CHECK_FORM_SAVE_REQUEST = "form-save-request"  # this helps in identifying that the POST request is saving form

class VMCQForm(forms.ModelForm):
    draft_statement = forms.CharField(widget=PagedownWidget(attrs={'placeholder': 'Question Statement', 'rows': 2}),
                                      strip=False)

    class Meta:
        model = Question
        fields = ['video_file', 'draft_statement', 'question_weight', 'question_difficulty']


class VMCQ(AbstractQuestion):
    """
    The class is to implement the Multiple Choice type Question.
    """
    CLASS_NAME = "VMCQ"
    CLASS_VERBOSE_NAME = "Video Based Multiple Choice Question"
    # POST Request Variable name as used in MCQ template
    DRAFT_OPTIONS = "draft_options"
    DRAFT_STATEMENT = "draft_statement"
    CORRECT_RESPONSE = "correct_option"


    @staticmethod
    def get_edit_view(request, question):
        """
        The function returns JSON reponse with 'content' for the body with a form
        which will be used to edit/add a new question.
        On success return to HttpResponseRedirect(reverse('edit')). 
        """
        question.question_type = VMCQ.CLASS_NAME
        template = loader.get_template('questions/vmcq-form.html')
        message = None
        # fill the variables from the POST if possible, else from the 
        # question
        # breakpoint()
        if question.draft_options_data and question.draft_options_data != '':
            options = json.loads(question.draft_options_data)
            expected_option_id = question.draft_expected_response
        else:
            options = [['option_1', ''], ['option_2', '']]
            expected_option_id = ''

        if request.method == "POST" and request.POST.get(CHECK_FORM_SAVE_REQUEST, False):
            valid = True
            form = VMCQForm(data = request.POST, instance=question)
            options_list = request.POST.getlist(VMCQ.DRAFT_OPTIONS)
            # following if-block might not be required?
            if VMCQ.DRAFT_OPTIONS not in request.POST or len(options_list) < 2:
                message = "Add at least two options!"
                valid = False
            expected_option_id = request.POST.get(VMCQ.CORRECT_RESPONSE,False)
            if not expected_option_id:
                message="Please add a correct option"
                valid = False
            if valid:
                # Store the option of the form as tuples (option_id, option_markdown)
                option_tuples = []
                for i in range(len(options_list)):
                    option = options_list[i]
                    option_tuples.append(("option_" + str(i + 1), option))

                if form.is_valid():
                    qs = form.save(commit=False)
                    qs.draft_expected_response = expected_option_id
                    qs.draft_options_data = json.dumps(option_tuples)
                    # if request.FILES.get('video_file'):
                    qs.save()
                    message = "The question is saved/updated successfully!"
                    return JsonResponse({'replace_content': "edit", 'message' : message, "file": True})

        else:
            form = VMCQForm(instance=question)
        context = {'form': form, 'options': options,
                               'expected_option_id': expected_option_id}

        context['qid'] = question.pk if question.pk else False
        content = template.render(context)
        return JsonResponse({'content': content, 'success': False, 'message': message})

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
        template = loader.get_template('questions/vmcq.html')
        context = {
            'qid': question.id,
            'statement': VMCQ.get_statement_html(question),
            'options': options,
            'video_file': question.video_file,
        }
        print(context)
        return template.render(context)

    @staticmethod
    def get_student_responded_view_html(question, response):
        options = json.loads(question.options_data)
        template = loader.get_template('questions/vmcq.html')
        context = {
            'qid': question.id,
            'statement': VMCQ.get_statement_html(question),
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
        template = loader.get_template('questions/vmcq.html')
        context = {
            'qid': question.id,
            'statement': VMCQ.get_statement_html(question),
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

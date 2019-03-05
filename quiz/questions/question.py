from django.http.response import HttpResponse

from abc import ABC, abstractmethod


class AbstractQuestion(ABC):
    """
    The class is to implement the Abstract Question
    """
    CLASS_NAME = "Question"
    CLASS_VERBOSE_NAME = "Question"

    # POST Request Variable name as used in templates
    DRAFT_OPTIONS = "draft_options"
    DRAFT_STATEMENT = "draft_statement"
    # use any sort of names which suits you and your template
    CORRECT_RESPONSE = "correct_option"

    @staticmethod
    @abstractmethod
    def get_edit_view(request, question):
        """
        The function returns the Manager view of the question as a django view response.
        On success return to HttpResponseRedirect(reverse('edit')). 
        """
        return HttpResponse("Not Implemented")

    @staticmethod
    @abstractmethod
    def get_statement_html(question):
        """
        Return the published html for the question's statement. This html is used in the Question Paper,
        Manager's view etc...
        :param question:
        :return: string : html representation of the statement of the question
        """
        return ''

    @staticmethod
    @abstractmethod
    def get_draft_statement_html(question):
        """
        Return the DRAFT html for the question's statement. This html is used in the in the Manager's
        view.
        :param question: Question class object
        :return: string : html representation of the draft statement of the question
        """

    @staticmethod
    @abstractmethod
    def get_student_view_html(question):
        """
        Return the complete html for the student. It is included in the quiz as form element.
        There should be a form field with the name same as the id of the question. This would be
        used to retrieve the user's response for the question.
        :param question: Question class object
        :return:
        """
        return ''

    @staticmethod
    @abstractmethod
    def get_student_responded_view_html(question, response):
        """
        Return the complete html for the student, same as 'get_student_view_html', but mark
        the given response in the form for the question.
        :param question: Question class object
        :return:
        """
        return ''

    @staticmethod
    @abstractmethod
    def get_marks(question, response):
        """
        Return the marks for the question.
        :param question:
        :param response:
        :return:
        """
        return 0

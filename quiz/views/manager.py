import json
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from quiz.utils.decorators import *
from ..forms import QuizSettingsForm
from ..models import QuizManager, Question
from ..questions import QUESTION_TYPE


GET_QUESTION_TYPE_NAME = 'question_type'



def index(request):
    manager = db.get_user(request)     # Save the Manager's details if doesn't exists already
    quiz = db.get_quiz(request)
    if not quiz:
        quiz = db.create_new_quiz(request)
    # Add the Manager as the QuizManager if not already
    if not QuizManager.objects.filter(quiz=quiz, manager=manager).exists():
        quiz_manager = QuizManager(quiz=quiz, manager=manager)
        quiz_manager.save()
        return new_manager_tour(request)  # return the home page for the new user
    return home(request)


def home(request):
    """
    The home view for the manager. It shows the latest live quiz if it exists.
    """
    quiz = db.get_quiz(request)
    if not quiz.published:
        message = 'You have not published the Quiz yet! <br/>Please click edit button to ' \
                  'start editing the quiz, or publish it!'
        return render(request, "manager.html", {"name": lti.get_user_name(request), 'message': message})

    # Show the questions of the quiz
    # TODO: show student view complete
    questions = db.get_questions_by_quiz(quiz)
    questionsHTML = ''
    count = 0
    for question in questions:
        question_type = QUESTION_TYPE[question.question_type]  # get the class for the question
        statement = question_type.get_statement_html(question)
        if statement != '':
            count+=1
            question_format = "<tr><td>{count}</td><td><h4> {statement} </h4></td> </tr>"
            questionsHTML += question_format.format(count=count, statement=statement)

    message = 'Please click edit button to start editing the quiz!!!'
    return render(
        request,
        "manager.html",
        {
            'questionsHTML': questionsHTML,
            'success': True,
            'message': message
        }
    )


# TODO : To be implemented
def new_manager_tour(request):
    """
    The view to show the tour to the iQuiz to the manager.
    """
    return render(
        request,
        "manager.html",
        {
            "name": lti.get_user_name(request),
            'message': 'Welcome! Please go through the documentation on how to use iQuiz, besides you '
                       'can just use it by playing with the buttons here and there!'}
    )


@csrf_exempt
@validate_manager
def edit_quiz_settings(request):
    """
    Renders the Settings page for the quiz
    """
    quiz_settings = db.get_quiz(request).quizsettings
    if request.method == "POST":
        form = QuizSettingsForm(request.POST, instance=quiz_settings)
        if form.is_valid():
            qs = form.save(commit=False)
            qs.save()
            return render(request, 'quiz-settings.html', {'form': form, 'success': True})
    else:
        form = QuizSettingsForm(instance=quiz_settings)
    return render(request, 'quiz-settings.html', {'form': form, 'success':False})


@csrf_exempt
@validate_manager
def edit(request):

    quiz = db.get_quiz(request)
    # Check if the quiz is ever attempted
    if quiz.isEverAttempted:
        return render(
            request,
            'manager.html',
            {
                'success': False,
                'message': 'The quiz cannot be edited as it is attempted by at least one student!'
            }
        )
    # show all the questions added till now to the manager with edit button
    questions = db.get_questions_by_quiz(quiz)
    questions_list = []
    for question in questions:
        question_dict = dict()
        question_type = QUESTION_TYPE[question.question_type]  # get the static class for the question
        draft = question_type.get_draft_statement_html(question)
        question_dict['draft'] = draft
        question_dict['qid'] = question.id
        questions_list.append(question_dict)
    return render(request, 'edit.html', {'questions': questions_list})


@csrf_exempt
@validate_manager
def edit_question(request, question=None):
    # Check if the quiz is ever attempted
    quiz = db.get_quiz(request)
    if quiz.isEverAttempted:
        return render(
            request,
            'manager.html',
            {
                'success': False,
                'message': 'The quiz cannot be edited as it is attempted by at least one student!'
            }
        )
    if question: 
        return question_type.get_edit_view(request, question)

    if 'qid' not in request.GET:
        return edit(request)

    try:
        question = Question.objects.get(id = request.GET.get('qid'), quiz=quiz)
    except Question.DoesNotExists:
        return edit(request)

    if request.GET.get('confirm_delete', False):
        # Delete the question and re render the edit page.
        question.delete()
        return edit(request)

    question_type = QUESTION_TYPE[question.question_type]
    return question_type.get_edit_view(request, question)


@csrf_exempt
@validate_manager
def add_question(request):
    """
    Creates a new question and returns the edit panel for the same.
    """
    quiz = db.get_quiz(request)
    if quiz.isEverAttempted:
        return render(
            request,
            'manager.html',
            {
                'success': False,
                'message': 'The quiz cannot be edited as it is attempted by at least one student!'
            }
        )

    question_type_name = request.GET.get(GET_QUESTION_TYPE_NAME, '')
    if question_type_name not in QUESTION_TYPE:
        return edit(request)
    question_type = QUESTION_TYPE[question_type_name]
    question = Question(quiz=quiz)        # create a new Question for the quiz
    quiz_questions = db.get_questions_by_quiz(quiz)

    if quiz_questions:
        last_question_index = quiz_questions.count() - 1
        question.serial_number = quiz_questions[last_question_index].serial_number + 1 #Set the serial number for the question
    return question_type.get_edit_view(request, question)


@validate_manager
def grades(request):
    quiz = db.get_quiz(request)
    responses = db.get_students_responses(request)  # get all the submitted responses
    attempts = [get_attempts_detail(response, quiz) for response in responses]
    return render(request, "grades.html", {'attempts': attempts})


@validate_manager
def publish(request):
    """
    Publish the quiz : copy all the draft question data columns to the live data columns.
    """
    confirm_publish = request.GET.get('confirm_publish', False)
    confirm_delete = request.GET.get('confirm_delete', False)

    if confirm_publish:
        quiz = db.get_quiz(request)
        quiz.published = True
        # Copy all the draft fields to the published fields
        questions = db.get_questions_by_quiz(quiz)
        for question in questions:
            question.statement = question.draft_statement
            question.options_data = question.draft_options_data
            question.expected_response = question.draft_expected_response
            question.published = True
            question.save()

        quiz.save()
        return render(request, "manager.html", 
            {
            "name": lti.get_user_name(request), 
            'message': "The quiz has been published and updated <br/>Please go to Home!"}
            )
    if confirm_delete:
        #delete the quiz
        quiz = db.get_quiz(request)
        quiz.delete()
        return HttpResponseRedirect(reverse('index',))

    return render(request, "publish.html")



def get_attempts_detail(response, quiz):
    """
    Function to return the dictionary with attempts details for given quiz
    """
    attempt = dict()
    attempt['id'] = response.id
    attempt['student'] = str(response.user)
    attempt['submission_time'] = response.submission_time
    attempt['duration'] = str(round((response.submission_time - response.start_time).total_seconds()//60)) + " mins" #minutes
    attempt['grade'] = get_grade(response, quiz)
    return attempt


def get_grade(response, quiz):
    total = db.get_quiz_total_marks(quiz)
    obtained = 0
    response_data = json.loads(response.response)
    for qid in response_data:
        question = Question.objects.get(id=int(qid))
        question_type = QUESTION_TYPE[question.question_type]
        obtained += question_type.get_marks(question, response_data[qid])
    grade = obtained/total
    return round(grade, 2)  # round the grade to 2 d.p
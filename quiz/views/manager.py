import json
import math
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect

from django.shortcuts import render
from django.http import JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from quiz.utils.decorators import *
from ..forms import QuizSettingsForm
from ..models import QuizManager, Question
from ..questions import QUESTION_TYPE
from . import student

GET_QUESTION_TYPE_NAME = 'question_type'
JSON_REQUEST = "json_request"   # the keyword every json requests for page should sends to get only body


@validate_manager
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
    return HttpResponseRedirect(reverse('home'))
    

@validate_manager
def home(request):
    """
    The home view for the manager. It shows the latest live quiz if it exists.
    """
    quiz = db.get_quiz(request)
    if not quiz:
        message = "Quiz not found! Please click the link from the LMS again to recreate the quiz"
        return render(request, "error.html", {'message': message})
    if not quiz.published:
        message = 'You have not published the Quiz yet! <br/>Please click edit button to ' \
                  'start editing the quiz, or publish it!'
        return render(request, "manager.html", {'message': message})

    # Show the questions of the quiz
    quiz_settings = db.get_quiz_settings(quiz)
    information = quiz_settings.information
    questions = db.get_published_questions(quiz)  # returns QuerySet of the published questions
    total_questions_number = questions.count()
    max_attempts = quiz_settings.maxAttempts
    duration = quiz_settings.duration

    questions_html = list()
    for question in questions:
        question_type = QUESTION_TYPE[question.question_type]
        html = question_type.get_student_view_html(question)  # Add the HTML form field input for the question
        questions_html.append((question.id, html))

    message = 'Please click edit button to start editing the quiz!!!'
    time_left = 0
    return render(
        request,
        "manager.html",
        {
            'questions_html': questions_html,
            'information': information,
            'success': True,
            'message': message,
            'time_left': time_left,
            'information': information,
            'max_attempts' : max_attempts,
            'total_questions_number' : total_questions_number,
            'duration' : duration,
        }
    )


# TODO : To be implemented
@validate_manager
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
def edit(request, message=None, success=False):
    quiz = db.get_quiz(request)
    # Check if the quiz is ever attempted
    if quiz.isEverAttempted:
        template = loader.get_template('message-body.html')
        content = template.render(
            {
                'success': success,
                'message': 'The quiz cannot be edited as it is attempted by at least one student!'
            }
        )
    else:
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

        template = loader.get_template('edit.html')
        content = template.render( {'questions': questions_list} )

    return JsonResponse({'content': content, 'message': message, 'success':success})


@csrf_exempt
@validate_manager
def edit_question(request, question=None):
    """
    Returns the JSON response with 'content' for the edit_question page
    """
    # Check if the quiz is ever attempted
    quiz = db.get_quiz(request)
    if quiz.isEverAttempted:
        message = 'The quiz cannot be edited as it is attempted by at least one student!'
        return json_message_html(message, False)
        
    if question: 
        question_type = QUESTION_TYPE[question.question_type]
        return question_type.get_edit_view(request, question)

    if 'qid' not in request.POST:
        # if a question_type is given, then create a new question of the given question type
        question_type_name = request.POST.get(GET_QUESTION_TYPE_NAME,'')
        if question_type_name not in QUESTION_TYPE:
            message = 'Really Sorry!! But the request seems to be invalid! Try again or contact admin!'
            return json_message_html(message)

        question_type = QUESTION_TYPE[question_type_name]
        question = Question(quiz=quiz)        # create a new Question for the quiz
        if request.FILES.get('video_file'):
            question.video_file = request.FILES.get('video_file')
        quiz_questions = db.get_questions_by_quiz(quiz)
        if quiz_questions:
            last_question_index = quiz_questions.count() - 1
            question.serial_number = quiz_questions[last_question_index].serial_number + 1 #Set the serial number for the question
    else:
        try:
            question = Question.objects.get(id = request.POST.get('qid'), quiz=quiz)
            question_type = QUESTION_TYPE[question.question_type]  
        except Question.DoesNotExists:
            return json_message_html("Invalid request!")

    if request.POST.get('confirm_delete', False):
        # Delete the question and re render the edit page.
        question.delete()
        delete_success_message = "The question is deleted successfully!"
        return edit(request, message=delete_success_message, success=True)

    
    return question_type.get_edit_view(request, question)



def json_message_html(message="Invalid Request!", success=False, redirect=None, timeout=None):
    template = loader.get_template('message-body.html')
    content = template.render(
        {
            'success': success,
            'message': message,
        }
    )
    if redirect:
        timeout = timeout if timeout else 5000  # timeout will be 5000 milliseconds if not provided
        array = {
        'content': content,
        'redirect': redirect,
        'timeout' : timeout
        }
    else:
        array = {'content' : content}
    return JsonResponse(array)


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
            'message.html',
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


@csrf_exempt
@validate_manager
def grades(request):
    """
    Function returns the view for grades and responses of all students for the quiz being viewed.
    It returns JSON response. It also checks if keyword "get_full_attempt_details_id" is in the request.GET,
    if so, then only the JSON content of that particular attempt is returned.
    """
    full_attempt_details_id = request.POST.get('full_attempt_details_id', False)  # if full attempt details for a particular id is requested
    if full_attempt_details_id: 
        return get_full_attempt_details(full_attempt_details_id) 

    page_num = int(request.POST.get('page_num', 0))
    per_page = int(request.POST.get('per_page', 10))
    if per_page > 100:
        per_page = 100  # limit the value of per_page to 100 
    # TODO: Can add filtering capacity for teacher, like show only the responses after a particular date... etc.
    quiz = db.get_quiz(request)
    responses = db.get_students_responses(request)  # get all the submitted responses
    total_responses_count = responses.count()
    total_pages_num = math.ceil(total_responses_count/per_page)
    final_responses = responses[page_num*per_page: (page_num+1)*per_page]
    attempts = [get_attempt_detail(response, quiz) for response in responses]

    template = loader.get_template('grades.html')
    context =  {'attempts': attempts, 
        'total_responses_count': total_responses_count, 
        'total_pages_num_list': range(total_pages_num), 
        'current_page_num' : page_num+1,
        'per_page' : per_page,
        'quiz_id': quiz.id,
        # 'download_allowed': True,
        # 'view_download_allowed': True,
        }
    context['full'] = request.POST.get(JSON_REQUEST, False)
    
    content = template.render(context)
    return JsonResponse({'content': content})


@csrf_exempt
@validate_manager
def publish(request):
    """
    Publish the quiz : copy all the draft question data columns to the live data columns.
    """
    confirm_publish = request.POST.get('confirm_publish', False)
    confirm_delete = request.POST.get('confirm_delete', False)
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
        message = "The quiz has been published and updated <br/>Please go to Home!"
        return json_message_html(message)

    if confirm_delete:
        #delete the quiz
        quiz = db.get_quiz(request)
        quiz.delete()
        return json_message_html("Perhaps everything comes to end! \
            Delete this link or refresh the page to create a new quiz here!", success = True)
    template = loader.get_template('publish.html')
    content = template.render()
    return JsonResponse({'content': content})




def get_attempt_detail(response, quiz):
    """
    Function to return the dictionary with attempts details for given response of given quiz
    """
    attempt = dict()
    attempt['id'] = response.id
    attempt['student'] = str(response.user)
    attempt['submission_time'] = response.submission_time
    attempt['duration'] = get_duration_time(response)
    attempt['grade'] = get_grade(response, quiz)
    return attempt


def get_duration_time(response):
    # breakpoint()
    return str(
        round((response.submission_time - response.start_time).total_seconds() // 60)) + " mins " \
            + str(int((response.submission_time - response.start_time).total_seconds() % 60)) + " secs"


@validate_manager
def get_full_attempt_details(request):
    """
    Function receives the AJAX requests from the manager for the full response details for the
    'attempt_id' given in the request.POST.
    """
    manager = lti.get_user(request)     # get the manager making the request
    quiz = lti.get_quiz(request)
    if not (request.POST and 'attempt_id' in request.POST):
        return JsonResponse({'content': '<h4>Invalid Request</h4>'})

    attempt_id = request.POST['attempt_id']
    try:
        response = Response.objects.get(id=attempt_id)
    except:
        response = None

    if not response or (manager not in db.get_managers(quiz)):  # check the manager indeed 'manages' the quiz to which the attempt is associated
        return JsonResponse(
            dict(content='<h4>Invalid Attempt ID, try again or please contact admin for resolution of the error.</h4>')
        )

    # Return the full details of the response
    attempt_details_full, question_paper = student.get_attempts_details_and_paper(quiz, response)
    template = loader.get_template('responded_question_paper.html')
    content = template.render({'attempt_details': attempt_details_full, 'question_paper': question_paper})
    return JsonResponse({'content': content})


def get_grade(response, quiz):
    total = db.get_quiz_total_marks(quiz)
    obtained = 0
    response_data = json.loads(response.response)
    for qid in response_data:
        question = Question.objects.get(id=int(qid))
        question_type = QUESTION_TYPE[question.question_type]
        most_recent_answer = response_data[qid][-1][0] # Selecting answer from Tuple (answer, timestamp)
        obtained += question_type.get_marks(question, most_recent_answer)
    grade = obtained/total * 100
    return round(grade, 2)  # round the grade to 2 d.p
import datetime
import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from pylti.common import post_message, generate_request_xml

from quiz.utils.decorators import *
from ..models import Question, Response, OutcomeServiceData
from ..questions import QUESTION_TYPE

CONSUMERS = settings.LTI_OAUTH_CREDENTIALS


@validate_user
def index(request):
    return home(request)


@validate_user
def home(request):
    student = db.get_user(request)
    quiz = db.get_quiz(request)
    # Save/Update the OutcomeServiceData in the database
    lis_result_sourcedid = lti.get_result_sourced_id(request)
    lis_outcome_service_url = lti.get_outcome_service_url(request)
    if lis_result_sourcedid and lis_outcome_service_url:
        # Check if outcomeServiceData object already exists, then update it.
        outcome_service, created = OutcomeServiceData.objects.get_or_create(user=student, quiz=quiz)
        outcome_service.lis_result_sourcedid = lti.get_result_sourced_id(request)
        outcome_service.lis_outcome_service_url = lti.get_outcome_service_url(request)
        outcome_service.save()

    quiz_settings = db.get_quiz_settings(quiz)
    information = quiz_settings.information
    attempts = get_attempts_detail(request)
    # Check if the student has attempt left or not, if the handle is not None, then
    # we need to return the handle itself.
    handle = handle_previous_attempt(request)
    if handle:
        return handle
    if quiz and quiz.published:
        return render(request, 'student.html', {'attempts': attempts, 'information': information})

    return render(request, 'error.html', {'success': False, 'message': "The quiz cannot be found! Please try later!"})


def resume_quiz(request, previous_attempt):
    """
    Function resumes the quiz which is live. It could be the attempt just started, or the
    previous live attempt.
    :param request: django request object
    :param previous_attempt: Response class object which represents the live attempt
    :return: Django request response
    """
    quiz = db.get_quiz(request)
    questions = db.get_published_questions(quiz)  # returns QuerySet of the published questions
    end_time_stamp = previous_attempt.end_time.timestamp()
    # time left in milliseconds if end_time_stamp is there
    time_left = (end_time_stamp - datetime.datetime.utcnow().timestamp()) * 1000 if end_time_stamp else None
    quiz_settings = db.get_quiz_settings(quiz)
    information = quiz_settings.information

    if questions.count() == 0:
        return render(
            request,
            "error.html",
            {
                "message": "The quiz doesn't have any question yet!!"
            }
        )

    questions_html = list()
    questions_statements = list()  # To be used for creating the Question paper
    question_ids = list()
    question_types = dict()
    responses = previous_attempt.get_response()  # get the responses of the student for this attempt
    answered_question_ids = []  # will be used to store the ids of the questions which are already answered

    for question in questions:
        question_type = QUESTION_TYPE[question.question_type]
        # Check if the question is already responded, then get the responded form html
        response = extract_response(responses, question.id)
        if response:
            # Add the HTML form field input for the question with response already selected
            html = question_type.get_student_responded_view_html(question, response)
            answered_question_ids.append(question.id)  # mark the question as answered by adding its id to list
        else:
            html = question_type.get_student_view_html(question)  # Add the HTML form field input for the question
        questions_html.append((question.id, html))
        question_ids.append(question.id)
        question_types[question.id] = question_type.CLASS_NAME
        questions_statements.append((question.id, question_type.get_statement_html(question)))

    return render(
        request,
        'quiz.html',
        {
            'questions_html': questions_html,
            'question_ids': question_ids,
            'question_statements': questions_statements,
            'question_types': question_types,
            'information': information,
            'time_left': time_left,
            'answered_question_ids': answered_question_ids
        }
    )


@csrf_exempt
@validate_user
def show_quiz(request):
    handler = handle_previous_attempt(request)
    if handler:
        return handler

    new_attempt = db.get_new_attempt(request)
    attempts = get_attempts_detail(request)
    if not new_attempt:
        return render(
            request,
            'student.html',
            {
                'quiz_not_allowed': True,
                'success': False,
                'message': 'No attempt left! Please view your grades.',
                'attempts': attempts
            }
        )
    else:
        return resume_quiz(request, new_attempt)


@csrf_exempt
@validate_user
def save_response(request):
    # To save the response from ajax request
    attempt = db.get_previous_attempt(request)
    if not attempt:
        message = "Your attempt has either expired or isn't valid!"
        return JsonResponse(
            {
                'redirect': '/student',
                'message': message,
                'time': 5000
            }
        )  # redirect after 5 seconds

    if 'submit' in request.POST:
        # if submit is in request.POST, then its time to submit the quiz!
        submit_response(request, attempt)

        message = "Your quiz has been submitted!"
        return JsonResponse(
            {'submit': 'success',
             'redirect': '/student',
             'message': message,
             'time': 5000
             }
        )
        # TODO: We can show the analytics of the quiz here

    # add the response to the Response object for the live attempt
    quiz = db.get_quiz(request)
    questions_id = db.get_published_questions_id(quiz)  # get the question ids for the quiz

    for qid_string in request.POST:
        # check that the student can only access the question of the quiz they are answering
        if qid_string.isdigit() and int(qid_string) in questions_id:
            attempt.add_or_update_response(qid_string, request.POST[qid_string])

    return JsonResponse({'success': 'true'})


def submit_response(request, attempt):
    """
    Submits the quiz
    :param request: django request object
    :param attempt: the Response object which is to be saved
    :return: None
    """
    attempt.submitted = True
    if attempt_time_valid(attempt):
        attempt.submission_time = datetime.datetime.utcnow()
    else:
        # if submission is beyond the allowed time, then save the end_time as submission time
        attempt.submission_time = attempt.end_time
    attempt.save()
    send_grade_to_lms(request, attempt)


def send_grade_to_lms(request, attempt):
    """
    Sends the grade to lms using xml.
    :param request: django request object
    :param attempt: the Response object whose data is to be sent
    :return: None if quiz is not graded.
    """
    quiz = db.get_quiz(request)
    quiz_settings = db.get_quiz_settings(quiz)
    student = db.get_user(request)
    if not quiz_settings.graded:
        return None
    outcome_service_url = lti.get_outcome_service_url(request)
    result_sourcedid = lti.get_result_sourced_id(request)
    # if outcome_service_url or result_sourcedid is not available in this request, search the database
    if not (outcome_service_url or result_sourcedid):
        try:
            outcome_service_data = OutcomeServiceData.objects.get(user=student, quiz=quiz)
            outcome_service_url = outcome_service_data.lis_outcome_service_url
            result_sourcedid = outcome_service_data.lis_result_sourcedid
        except OutcomeServiceData.DoesNotExists:
            return  # cannot send the grade as outcome_service_url is not available

    consumer_key = lti.get_oauth_consumer_key(request)
    message_identifier_id = "iquiz_grade"  # TODO: Is this correct?
    operation = "replaceResult"
    score = get_grade(attempt, quiz)
    xml = generate_request_xml(
        message_identifier_id=message_identifier_id,
        operation=operation,
        lis_result_sourcedid=result_sourcedid,
        score=score
    )
    if not post_message(
            CONSUMERS,
            consumer_key,
            outcome_service_url,
            xml
    ):
        raise Exception("Some error occurred while sending grade to the lms.")
        


@csrf_exempt
def save_timing_details(request):
    # TODO: Implement this for data collection
    # to save the timing details from the ajax request
    attempt = db.get_previous_attempt(request)
    if not attempt:
        message = "Your attempt has either expired or isn't valid!"
        return JsonResponse(
            {
                'redirect': '/student',
                'message': message,
                'time': 5000}
        )  # redirect after 5 seconds
    if 'question_switched' in request.POST:
        # get the id of the question to which screen is switched
        pass


@csrf_exempt
@validate_user
def attempt_details(request):
    # Viewing full response is allowed if :
    # 1. If deadline is not set,
    # 2. If deadline is set and is due.
    # 3. If maxAttempt is not set
    # 4. If all_attempt are exhausted (maxAttempts should already be set)

    quiz = db.get_quiz(request)
    user = db.get_user(request)
    quiz_settings = db.get_quiz_settings(quiz)
    full_response_allowed = \
        not quiz_settings.deadline \
        or quiz_settings.deadline < datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) \
        or not quiz_settings.maxAttempts \
        or quiz_settings.maxAttempts <= db.get_used_attempt_number(quiz, user)

    if not (request.POST and 'attempt_id' in request.POST):
        return JsonResponse({'content': '<h4>Invalid Request</h4>'})

    attempt_id = request.POST['attempt_id']
    try:
        response = Response.objects.get(id=attempt_id)
    except:
        pass

    if not response or (lti.is_student(request) and response.user != user):
        return JsonResponse(
            dict(content='<h4>Invalid Attempt ID, try again or please contact admin for resolution of the error.</h4>')
        )

    if not full_response_allowed:
        # Return the summary for the response
        attempt_details_summary = get_attempt_stats(quiz, response)
        template = loader.get_template('attempt-grade.html')
        content = template.render({'attempt_details': attempt_details_summary})
        return JsonResponse({'content': content})
    else:
        # Return the full details of the response
        attempt_details_full, question_paper = get_attempts_details_and_paper(quiz, response)
        template = loader.get_template('responded_question_paper.html')
        content = template.render({'attempt_details': attempt_details_full, 'question_paper': question_paper})
        return JsonResponse({'content': content})


# Helper Functions
def get_attempts_detail(request):
    """
    Function to return the dictionary with attempts details for the user (Student).
    """
    quiz = db.get_quiz(request)
    responses = db.get_submitted_responses(request)
    attempts = []
    for response in responses:
        attempt = dict()
        attempt['id'] = response.id
        attempt['submission_time'] = response.submission_time
        attempt['duration'] = str(
            round((response.submission_time - response.start_time).total_seconds() // 60)) + " mins"  # minutes
        attempt['grade'] = get_grade(response, quiz)
        attempts.append(attempt)
    return attempts


def get_attempts_details_and_paper(quiz, response_object):
    """
    Function to return the dictionary with FULL attempts details for the user (Student).
    """
    attempt = get_attempt_stats(quiz, response_object)  # get basic stats and then we will add more data
    attempt['id'] = response_object.id
    attempt['start_time'] = response_object.start_time
    attempt['duration'] = str(
        round((response_object.submission_time -
               response_object.start_time).total_seconds() // 60)) + " minutes"  # minutes
    allowed_time = db.get_quiz_settings(quiz).duration
    attempt['allowed_time'] = str(allowed_time) + " minutes" if allowed_time else "Unlimited"
    attempt['total_questions'] = attempt['correct'] + attempt['incorrect'] + attempt['unanswered']
    attempt['total_grade_percent'] = str(attempt['total_grade'] * 100) + "%"

    # now we shall form the responded question paper
    questions_html = list()
    questions = db.get_published_questions(quiz)
    response_data = response_object.get_response()
    for question in questions:
        question_type = QUESTION_TYPE[question.question_type]
        response = extract_response(response_data, question.id)
        html = question_type.get_student_responded_paper_view_html(question, response)
        questions_html.append((question.id, html))
    return attempt, questions_html


def attempt_time_valid(attempt):
    return datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc) <= attempt.end_time + datetime.timedelta(seconds=END_TIME_RELAXATION)


def get_grade(response, quiz):
    total = db.get_quiz_total_marks(quiz)
    obtained = 0
    response_data = json.loads(response.response)
    for qid in response_data:
        question = Question.objects.get(id=int(qid))
        question_type = QUESTION_TYPE[question.question_type]
        obtained += question_type.get_marks(question, response_data[qid])
    grade = obtained / total
    return round(grade, 2)  # round the grade to 2 d.p


def get_attempt_stats(quiz, response):
    """
    Returns the stats for the quiz and given response
    :param quiz: Quiz model object
    :param response: Response model object
    :return:
    """
    total_marks = 0
    correct_answer = 0
    incorrect_answer = 0
    total_number = Question.objects.filter(quiz=quiz, published=True).count()
    response_data = response.get_response()
    for qid in response_data:
        try:
            question = Question.objects.get(id=int(qid))
        except Question.DoesNotExists:
            # there might be other kind of data in response_data we don't care about
            continue
        question_type = QUESTION_TYPE[question.question_type]
        marks = question_type.get_marks(question, extract_response(response_data, qid))
        total_marks += marks
        if marks > 0:
            correct_answer += 1
        else:
            incorrect_answer += 1
    grade = round(total_marks / db.get_quiz_total_marks(quiz), 2)
    unanswered = total_number - (correct_answer + incorrect_answer)
    return dict(total_grade=grade, correct=correct_answer, incorrect=incorrect_answer, unanswered=unanswered)


def extract_response(responses, qid):
    qid = str(qid)
    if qid in responses:
        return responses[qid]
    else:
        return None


def handle_previous_attempt(request):
    previousAttempt = db.get_previous_attempt(request)
    if previousAttempt:
        if attempt_time_valid(previousAttempt):
            # The previous attempt is live, so send the responded answers which exists with quiz.
            return resume_quiz(request, previousAttempt)
        else:
            # The last attempt is timed out, so submit the previous attempt and re-render the index.
            previousAttempt.submission_time = previousAttempt.end_time  # Set the submission time to be the end time of the attempt
            previousAttempt.submitted = True
            previousAttempt.save()
            return render(request, 'student.html', {'success': False,
                                                    'message': 'Your last quiz attempt was not submitted properly! It is timed out!<br/>Please view your grades.'})
    return False

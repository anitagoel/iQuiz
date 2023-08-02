import datetime
import json
from django.utils import timezone

from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pylti.common import post_message, generate_request_xml
from django.http import HttpResponseNotFound

from quiz.utils.decorators import *
from ..models import Question, Response, OutcomeServiceData, Answer, PromptResponse
from ..questions import QUESTION_TYPE

CONSUMERS = settings.LTI_OAUTH_CREDENTIALS
CLEAR_RESPONSE = "clear_response"   # POST attribute for clearing the response (used by save_response function)


@validate_user
def index(request):
    return HttpResponseRedirect('student')


@validate_user
def home(request, message=None):
    student = db.get_user(request)
    quiz = db.get_quiz(request)
    if quiz:
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
        questions = db.get_published_questions(quiz)  # returns QuerySet of the published questions
        total_questions_number = questions.count()
        max_attempts = quiz_settings.maxAttempts
        duration = quiz_settings.duration
        quiz_not_allowed = False
        if max_attempts != None:
            if len(attempts) >= max_attempts:
                quiz_not_allowed = True

        # Check if the student has attempt left or not, if the handle is not None, then
        # we need to return the handle itself.
        analytics_button = True if db.get_used_attempt_number(quiz, student) > 1 else False
        handle = handle_previous_attempt(request)
        if handle:
            return handle
        if quiz and quiz.published:
            return render(request, 'student.html', {
                'attempts': attempts, 
                'quiz_not_allowed': quiz_not_allowed,
                'information': information,
                'max_attempts' : max_attempts,
                'total_questions_number' : total_questions_number,
                'duration' : duration,
                'analytics_button': analytics_button,
                'message' : message
                })

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
    quiz_settings = db.get_quiz_settings(quiz)
    questions = db.get_published_questions(quiz, random=quiz_settings.randomizeQuestionOrder)  # returns QuerySet of the published questions
    end_time_stamp = previous_attempt.end_time.timestamp()
    # time left in milliseconds if end_time_stamp is there
    time_left = (end_time_stamp -  datetime.datetime.utcnow().timestamp()) * 1000 if end_time_stamp else None
    information = quiz_settings.information
    total_questions_number = questions.count()

    if total_questions_number == 0:
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
    question_types = list()
    responses = previous_attempt.get_response()  # get the responses of the student for this attempt
    answered_question_ids = []  # will be used to store the ids of the questions which are already answered
    question_time_limits = {}
    promptQuestions = list(map(lambda prompt: prompt.occur_before_question, db.get_prompts_by_quiz(quiz)))

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
        questions_html.append((question.id, html, question.question_weight))
        question_ids.append(question.id)
        question_types.append((question.id, question_type.CLASS_NAME))
        questions_statements.append((question.id, question_type.get_statement_html(question)))
        if question.question_time_limit == 0:
            # Setting time limit as -1 for questions which doesnot have time limit
            question_time_limits[question.id] = -1
        else:
            answer = Answer.objects.filter(question=question, response=previous_attempt).first()
            if answer:
                # Calculating time left to answer from the time spent to view the question
                question_time_left = question.question_time_limit - answer.time_spent
                question_time_limits[question.id] = question_time_left if question_time_left >=0 else 0
                # TODO: create a list of answered timed questions to prevent student changing the answer if he answered in less seconds
            else:
                # Time left is the time set by teacher
                question_time_limits[question.id] = question.question_time_limit
    
    context =  {
            'questions_html': questions_html,
            'question_ids': question_ids,
            'question_statements': questions_statements,
            'question_types': question_types,
            'information': information,
            'time_left': time_left,
            'answered_question_ids': answered_question_ids,
            'question_time_limits': question_time_limits,
            'prompt_questions': promptQuestions,
        }

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        template = loader.get_template('quiz-body.html')
        content = template.render(context)
        return JsonResponse({'content' : content})
    else:
        return render(request, 'quiz.html', context)


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
def prompt(request):
    quiz = db.get_quiz(request)
    prompts = db.get_prompts_by_quiz(quiz)
    response = db.get_previous_attempt(request)
    if request.content_type == 'application/json' and response:
        data = json.loads(request.read().decode())
        id = int(data.get('id'))
        prompt_response = data.get('response')
        promptResponse = PromptResponse(response = response, prompt = prompts.get(pk=id), prompt_response=prompt_response)
        promptResponse.events = data.get('events')
        promptResponse.save()
        return JsonResponse({
            'success': True
        })
    questionNumber = int(request.GET.get('questionNumber'))
    prompt = prompts.get(occur_before_question = questionNumber)
    promptAnswered = PromptResponse.objects.filter(response = response, prompt = prompt)
    if not prompt or promptAnswered:
        return HttpResponseNotFound("Either no prompt available or you have answered already!")
    
    return JsonResponse({
        'question': prompt.question,
        'id': prompt.id
    })


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

    if CLEAR_RESPONSE in request.POST:
        qid = request.POST.get(CLEAR_RESPONSE)
        attempt.clear_response(qid)
        return JsonResponse({'success':'true'})

    # add the response to the Response object for the live attempt
    quiz = db.get_quiz(request)
    questions_id = db.get_published_questions_id(quiz)  # get the question ids for the quiz
    # check if the request has a viewing-time-qid and the time in the POST
    qid_viewing_time = request.POST.get("viewing-time-qid", False)
    time_duration = request.POST.get("viewing-time-duration", False)
    if qid_viewing_time and time_duration:
        qid_viewing_time = int(qid_viewing_time)
        time_duration = int(float(time_duration))     # get time duration in seconds
        question = Question.objects.get(pk = qid_viewing_time)      # get the question with id qid_viewing_time
        if Answer.add_time_spent(attempt, question, time_duration):
            # Answer.set_answer(attempt, question)
            return JsonResponse({'success':'true'})
        return JsonResponse({'success': 'false'})
    
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
        print(data)
        events = data.get('events', [])
        if events:
            del data['events']
        for qid_string in data:
            # check that the student can only access the question of the quiz they are answering
            # TODO: Check the response request.POST[qid_string] is valid! It seems like a
            # security flaw that the data from the POST is directly saved in the database
            # without any sanity check at all!
            if qid_string.isdigit() and int(qid_string) in questions_id:
                attempt.add_or_update_response(qid_string, data[qid_string], events)

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
    # It is very unlikely (or maybe impossible) that outcome_service_url will not be in the request itself,
    # but there is no harm in searching database if we can't find it in the current request ( or is there? )
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

    # add the last successfully sent response id and time to the outcome_service_data
    outcome_service_data, _ = OutcomeServiceData.objects.get_or_create(user=student, quiz=quiz)
    outcome_service_data.response_sent = attempt
    outcome_service_data.outcome_send_time = datetime.datetime.utcnow()
        


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
    # Viewing full response is allowed to student if :
    # 1. If deadline is not set,
    # 2. If deadline is set and is due.
    # 3. If maxAttempt is not set
    # 4. If all_attempt are exhausted (maxAttempts should already be set)

    quiz = db.get_quiz(request)
    user = db.get_user(request)
    quiz_settings = db.get_quiz_settings(quiz)
    full_response_allowed = \
        not quiz_settings.deadline \
        or quiz_settings.deadline <  datetime.datetime.utcnow() \
        or not quiz_settings.maxAttempts \
        or quiz_settings.maxAttempts <= db.get_used_attempt_number(quiz, user)

    if not (request.POST and 'attempt_id' in request.POST):
        return JsonResponse({'content': '<h4>Invalid Request</h4>'})

    attempt_id = request.POST['attempt_id']
    prompts = []
    try:
        response = Response.objects.get(id=attempt_id)
        prompts = PromptResponse.objects.filter(response=response)
    except Exception as exc:
        print(exc)
        pass

    if not response or (lti.is_student(request) and response.user != user):
        return JsonResponse(
            dict(content='<h4>Invalid Attempt ID, try again or please contact admin for resolution of the error.</h4>')
        )

    # TODO: If the user is manager, make sure that the manager is indeed manager of the associated user id.
    if lti.is_manager(request):
        full_response_allowed = True    # manager always sees the full response

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
        content = template.render({'attempt_details': attempt_details_full, 'question_paper': question_paper, 'prompts': prompts})
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
        attempt['duration'] = get_duration_time(response)
        attempt['grade'] = get_grade(response, quiz)
        attempts.append(attempt)
    return attempts


def get_duration_time(response):
    return str(
        round((response.submission_time - response.start_time).total_seconds() // 60)) + " mins " \
            + str(int((response.submission_time - response.start_time).total_seconds() % 60)) + " secs"


def get_attempts_details_and_paper(quiz, response_object, get_time_spent=False):
    """
    Function to return the dictionary with FULL attempts details for the user (Student).
    """
    attempt = get_attempt_stats(quiz, response_object)  # get basic stats and then we will add more data
    attempt['id'] = response_object.id
    attempt['start_time'] = response_object.start_time
    attempt['duration'] = get_duration_time(response_object)
    allowed_time = db.get_quiz_settings(quiz).duration
    attempt['allowed_time'] = str(allowed_time) + " minutes" if allowed_time else "Unlimited"
    # Check if the total_grade is calculated or Shown after exam ends
    if attempt['showAnswer']:
        # Grade is calculated so convert to percentage
        attempt['total_grade_percent'] = str(attempt['total_grade'] * 100) + "%"
    else:
        attempt['total_grade_percent'] = attempt['total_grade']

    # now we shall form the responded question paper

    questions_html = list()
    questions = db.get_published_questions(quiz)
    response_data = response_object.get_response()
    time_spent = list()
    question_marks = list()
    question_statements = list()

    for question in questions:
        question_type = QUESTION_TYPE[question.question_type]
        response = extract_response(response_data, question.id)
        html = question_type.get_student_responded_paper_view_html(question, response, showAnswer=quiz.quizsettings.showAnswersAfterAttempt)
        questions_html.append((question.id, html))
        question_statements.append(question_type.get_statement_html(question))
        print(html)
        if get_time_spent:
            time_spent.append(Answer.get_time_spent(response_object, question))
            if (response is None):
                # if the question is not attempted, add None to the question_marks list
                question_marks.append("null")
                continue
            # if the question HAD a response, add its marks
            marks = question_type.get_marks(question, response)
            question_marks.append(marks)

    if get_time_spent:
        return attempt, questions_html,question_statements, time_spent, question_marks
    
    return attempt, questions_html


def attempt_time_valid(attempt):
    return  datetime.datetime.utcnow()  <= attempt.end_time + datetime.timedelta(seconds=END_TIME_RELAXATION)


def get_grade(response, quiz):
    total = db.get_quiz_total_marks(quiz)
    obtained = 0
    response_data = json.loads(response.response)
    for qid in response_data:
        question = Question.objects.get(id=int(qid))
        question_type = QUESTION_TYPE[question.question_type]
        most_recent_answer = extract_response(response_data, qid) # Selecting answer from Tuple (answer, timestamp)
        obtained += question_type.get_marks(question, most_recent_answer)
    grade = obtained / total * 100 # Todo: Should it be multiplied?
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
    if quiz.quizsettings.showAnswersAfterAttempt:
        # Student allowed to see answer and hence the grade after attending quiz
        return dict(total_grade=grade, correct=correct_answer, incorrect=incorrect_answer, 
                    unanswered=unanswered, total_questions=total_number, showAnswer=True)
    return dict(total_grade='Shown after exam ends', unanswered=unanswered, total_questions=total_number, showAnswer=False)


def extract_response(responses, qid):
    qid = str(qid)
    if qid in responses and len(responses[qid]) > 0:
        return responses[qid][-1][0]
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


@csrf_exempt
@validate_user
def attempt_analytics(request):
    #TODO: Add checks if viewing analytics is allowed or not like attempt_details
    quiz = db.get_quiz(request)
    user = db.get_user(request)
    quiz_settings = db.get_quiz_settings(quiz)
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

    # Return the full details of the response
    attempt_details_full, question_paper, question_statements, time_spent,question_marks = get_attempts_details_and_paper(quiz, response, True)

    template = loader.get_template('attempt_analytics_ajax.html')
    content = template.render({
        'attempt_details': attempt_details_full, 
        'question_paper': question_paper, 
        'time_spent': time_spent, 
        'question_marks':question_marks, 
        'question_statements':question_statements
        }
    )
    
    return JsonResponse({'content': content})


@csrf_exempt
@validate_user
def analytics_page(request):
    #TODO: Add checks if viewing analytics is allowed or not like attempt_details
    quiz = db.get_quiz(request)
    user = db.get_user(request)
    quiz_settings = db.get_quiz_settings(quiz)

    attempts = Response.objects.filter(quiz=quiz, user = user)
    total_attempts  = attempts.count()
    if (total_attempts == 1):
        #only one attempt
        return home(request, "Analytics can only be shown if there are more than one attempts!")

    response_first = attempts[total_attempts - 1]    # last attempt
    response_second = attempts[total_attempts - 2]   # second last attempt

    # Return the full details of the response
    attempt_details_full_first, question_paper_first, question_statements, time_spent_first ,question_marks_first = get_attempts_details_and_paper(quiz, response_first, True)

    attempt_details_full_second, question_paper_second, question_statements, time_spent_second ,question_marks_second = get_attempts_details_and_paper(quiz, response_second, True)

    template = loader.get_template('analytics_page.html')
    content = template.render({
        'attempt_details_first': attempt_details_full_first, 
        'question_paper_first': question_paper_first, 
        'time_spent_first': time_spent_first, 
        'question_marks_first':question_marks_first, 
        'attempt_details_second': attempt_details_full_second, 
        'question_paper_second': question_paper_second, 
        'time_spent_second': time_spent_second, 
        'question_marks_second':question_marks_second, 
        'question_statements':question_statements
        }
    )
    return HttpResponse(content)


def get_average_time_spent_for_all_attempt(quiz):
    return 0


@csrf_exempt
def questionVisitTime(request):
    response = db.get_previous_attempt(request)
    question_id = request.POST.get('qid')
    visit_timestamps = response.questions_start_time.get(question_id, [])
    timestamp = datetime.datetime.utcnow().timestamp()
    visit_timestamps.append(timestamp)
    response.questions_start_time.update({ question_id: visit_timestamps })
    response.save()
    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["POST"])
def tabSwitchCount(request):
    response = db.get_previous_attempt(request)
    if response == False:
        return JsonResponse({'success': False})
    qid = request.POST.get("qid")
    count = response.tab_switch_count.get(qid, 0) + 1
    response.tab_switch_count[qid] = count
    response.save()
    return JsonResponse({'success': True})
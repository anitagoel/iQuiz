from django.db.models import Sum

from quiz.utils import lti_utils as lti
from quiz.models import Quiz, LTIUser, QuizSettings, Question, Response, QuizManager


def get_quiz(request):
    """
    Return the non-archived quiz if the resourceLinkId and contextId pair exists, if not, then check whether the resourceLinkId exists. If it
    does, then a new quiz is to be created which would be copy of the latest non archived version of the quiz with given resourceLinkId 
    return new quiz.
    """
    live_quiz = Quiz.objects.filter(consumer_key = lti.get_oauth_consumer_key(request), resourceLinkId = lti.get_resource_link_id(request), contextId = lti.get_context_id(request))
    if live_quiz.exists():
        return live_quiz.latest()

    # The resourceLinkId and the contextId pair doesn't exists, check whether the resourceLinkId exists.
    if Quiz.objects.filter(consumer_key = lti.get_oauth_consumer_key(request), resourceLinkId = lti.get_resource_link_id(request)).exists():
        # The quiz link is being migrated to another Context (new course term), hence the non-archived
        # latest quiz with same resourceLinkId has to be copied over as a new Quiz.
        quiz = create_new_quiz(request)
        latest_quiz = Quiz.objects.filter(consumer_key = lti.get_oauth_consumer_key(request), resourceLinkId = lti.get_resource_link_id(request)).latest()
        # copy all the settings of the latest quiz associated with the RESOURCE LINK ID.
        quiz_settings = QuizSettings.objects.get(quiz = quiz)
        quiz_settings.duration = latest_quiz.duration
        quiz_settings.timeBetweenAttempt = latest_quiz.timeBetweenAttempt
        quiz_settings.maxAttempts = latest_quiz.maxAttempts
        quiz_settings.graded = latest_quiz.graded
        quiz_settings.save()
        #TODO: Copy all the questions , doing it manually to avoid any useless trouble: is it the right way?
        questions = get_questions_by_quiz(latest_quiz)
        for question in questions:
            new_question = Question()
            new_question.quiz = question.quiz      # change the quiz to the new quiz
            new_question.question_type = question.question_type
            new_question.serial_number = question.serial_number
            new_question.question_weight = question.question_weight 
            new_question.statement = question.statement
            new_question.options_data = question.options_data
            new_question.expected_response = question.expected_response
            new_question.other_data = question.other_data
            new_question.published = question.published
            new_question.save()

        return quiz

    # The quiz doesn't exists for associated request! Return False
    return False


def create_new_quiz(request):
    """
    Creates a new quiz and its default settings for the given request, and returns the quiz.
    """
    quiz = Quiz() #New Quiz is created
    quiz.resourceLinkId = lti.get_resource_link_id(request)
    quiz.consumer_key = lti.get_oauth_consumer_key(request)
    quiz.contextId = lti.get_context_id(request)
    quiz.save() #Save the Quiz
    quizSettings = QuizSettings(quiz = quiz)
    quizSettings.save()
    return quiz


def get_user(request):
    """
    Return the user associated with give request if it exists, or create a new user and return it.
    It also stores/updates the Outcome service data in the database.
    """
    userId = lti.get_user_id(request)
    if not userId:
        return False
    ltiUserList = LTIUser.objects.filter(consumer_key = lti.get_oauth_consumer_key(request),  userId = userId)
    if ltiUserList.count() == 0:
        ltiUser = LTIUser()
        ltiUser.userId = lti.get_user_id(request)
        ltiUser.consumer_key = lti.get_oauth_consumer_key(request)
        ltiUser.name = lti.get_user_name(request)
        ltiUser.email = lti.get_user_email(request)
        ltiUser.role = lti.get_user_role(request)
        ltiUser.save() #Save the ltiUser
    else:
        ltiUser = ltiUserList[0]
    return ltiUser


def get_questions_by_quiz(quiz):
    return Question.objects.order_by('serial_number').filter(quiz = quiz)


def get_published_questions(quiz, random=None):
    """
    Returns the QuerySet of the published questions for the given quiz
    """
    questions = get_questions_by_quiz(quiz) #Questions are ordered by serial number
    if random:
        return questions.filter(published = True).order_by('?')
    return questions.filter(published = True)


def get_published_questions_id(quiz):
    """
    Returns the list of the ids of the published questions for the given quiz
    """
    questions = get_published_questions(quiz) #Questions are ordered by serial number
    question_ids = []
    for question in questions:
        question_ids.append(question.id)
    return question_ids


def get_previous_attempt(request):
    """
    Returns the non-submitted Response/Attempt for the given user/student as identified by the request.
    """
    responses = Response.objects.filter(quiz = get_quiz(request), user = get_user(request), submitted = False)
    if responses:
        attempt = responses.latest()
        return attempt
    return False


def get_new_attempt(request):
    """
    Returns a new Response/attempt.
    If the max attempt number is not set, then previous attempt is deleted.
    """
    quiz, user = get_quiz(request), get_user(request)
    quiz_settings = QuizSettings.objects.get(quiz = quiz)
    if not quiz_settings.maxAttempts:
        # Delete the last attempt and return a new attempt object if maxAttempts isn't set
        last_response = Response.objects.filter(quiz = quiz, user=user)
        if last_response:
            last_response.delete() # Delete the response
    else:
        used_attempt_number = get_used_attempt_number(quiz, user)
        max_attempts  = quiz_settings.maxAttempts
        if max_attempts and used_attempt_number >= max_attempts:
            # New attempt cannot be allowed, return False
            return False
    # Create a new Response and return.
    attempt = Response(quiz = quiz, user = user)
    attempt.set_end_time()
    attempt.save()

    # set isEverAttempted variable of Quiz to be True if not already
    if not quiz.isEverAttempted:
        quiz.isEverAttempted = True
        quiz.save()

    return attempt


def get_used_attempt_number(quiz, user):
    return Response.objects.filter(quiz=quiz, user = user).count()


def get_submitted_responses(request):
    responses = Response.objects.filter(quiz = get_quiz(request), user = get_user(request), submitted = True).order_by('-start_time')
    if responses:
        return responses
    return []


def get_students_responses(request):
    """
    Returns the last response of all students in the quiz
    """
    quiz = get_quiz(request)
    responses = Response.objects.filter(quiz=quiz, submitted=True).order_by('-start_time')
    return responses


def get_quiz_settings(quiz):
    return QuizSettings.objects.get(quiz=quiz)


def get_quiz_total_marks(quiz):
    """
    Returns the total marks of the quiz by adding weight of all questions in the quiz.
    :param quiz:
    :return: number : total marks
    """
    # TODO: Wouldn't it be better to store the total marks in a table like cache?
    questions = get_published_questions(quiz)
    total = questions.aggregate(Sum('question_weight'))['question_weight__sum']
    return total


def get_managers(quiz):
    """
    Returns the query set managers of the given quiz
    """
    managers = QuizManager.objects.filter(quiz=quiz)
    return managers
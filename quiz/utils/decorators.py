import datetime

from django.http import HttpResponseRedirect

from quiz.utils import lti_utils as lti, db_utils as db

END_TIME_RELAXATION = 30 #SECONDS relaxation for submission of quiz due to server delay

###TODO: Use decorators ###
#####Decorators#####


def validate_user(func):
    """
    Validates that the user is student or manager
    """
    def validator(request, *args, **kwargs):
        user = db.get_user(request)
        if not user or (not lti.is_manager(request) and not lti.is_student(request)):
            # Invalid access attempt
            return HttpResponseRedirect('/')
        return func(request, *args, **kwargs)
    return validator


def validate_manager(func):
    """
    Validates that the user is manager
    """
    def validator(request, *args, **kwargs):
        user = db.get_user(request)
        if not user or not lti.is_manager(request):
            # Invalid access attempt
            return HttpResponseRedirect('/')
        return func(request, *args, **kwargs)

    return validator


def attempt_exists(func):
    """
    Validates that the attempt of the user exists
    """
    def validator(request, *args, **kwargs):
        if not db.get_previous_attempt(request):
            return HttpResponseRedirect('/')
        return func(request, *args, **kwargs)
    return validator


def attempt_valid(func):
    """
    Validates that the attempt of the user is valid, i.e., it is not timed out
    """
    def validator(request, *args, **kwargs):
        previous_attempt = db.get_previous_attempt(request)
        if not previous_attempt:
            return HttpResponseRedirect('/student')
        if datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) <= previous_attempt.end_time + datetime.timedelta(seconds = END_TIME_RELAXATION):
            return HttpResponseRedirect('/student')
        return func(request, *args, **kwargs)
    return validator

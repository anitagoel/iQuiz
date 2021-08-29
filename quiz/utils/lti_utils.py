"""
The file provides various functions for dealing with LTI requests
"""
import re

RESOURCE_LINK_ID = "resource_link_id"
RESOURCE_LINK_TITLE = 'resource_link_title'
CONTEXT_TITLE = "context_title"
CONTEXT_ID = "context_id"
CONTEXT_LABEL = "context_label"
OAUTH_CONSUMER_KEY = 'oauth_consumer_key'
QUIZ_NAME = "custom_component_display_name"  # optionally provided by Open EdX

USER_ID = "user_id"
USER_EMAIL = "lis_person_contact_email_primary"
# USER_NAME = "lis_person_sourcedid"
USER_NAME = 'lis_person_name_full'

RESULT_SOURCE_ID = "lis_result_sourcedid"
OUTCOME_SERVICE_URL = 'lis_outcome_service_url'
ROLES = "roles"

MANAGER_ROLES = ["instructor", "administrator", "faculty", "staff"]
STUDENT_ROLES = ["learner", "student"]

params_to_save = [
    RESOURCE_LINK_ID, 
    RESOURCE_LINK_TITLE,
    CONTEXT_TITLE, 
    CONTEXT_ID, 
    CONTEXT_LABEL, 
    OAUTH_CONSUMER_KEY,  
    QUIZ_NAME, 
    USER_ID, 
    USER_EMAIL, 
    USER_NAME, 
    RESULT_SOURCE_ID, 
    OUTCOME_SERVICE_URL
]

MANAGER = "Instructor"
STUDENT = "Student"
# MANAGER_AS_STUDENT = "Manager_As_Student" #This new role will be used by the Manger to view the Quiz as the Student
# UNKNOWN = "Unknown"


def save_launch_request_session(request):
    """
    Saves the launch request parameters in the session.
    """
    for param in params_to_save:
        if param in request.POST:
            request.session[param] = request.POST[param]
        elif param in request.session:
            del request.session[param]

    if ROLES in request.POST and request.POST[ROLES].lower() in MANAGER_ROLES:
        request.session[ROLES] = MANAGER
    elif ROLES in request.POST and request.POST[ROLES].lower() in STUDENT_ROLES:
        request.session[ROLES] = STUDENT
    else:
        raise Exception("Trying to save a request with invalid role!")


def is_student(request):
    if ROLES in request.session and request.session[ROLES] == STUDENT:
        return True
    return False


def is_manager(request):
    if ROLES in request.session and request.session[ROLES] == MANAGER:
        return True
    return False


def get_user_role(request):
    if is_student(request):
        return STUDENT
    elif is_manager(request):
        return MANAGER


def get_resource_link_id(request):
    link = None
    if RESOURCE_LINK_ID in request.POST:
        link = request.POST[RESOURCE_LINK_ID]
    if RESOURCE_LINK_ID in request.session:
        link = request.session[RESOURCE_LINK_ID]
    # this is the resource link id pattern. Used because openEdx is sending different resource link id
    # for the teacher and student (e.g., prefixed with url in case of teacher?)
    link_pattern = r'-{0,1}\w*$'
    if link:
        return re.search(link_pattern, link).group()


def get_context_title(request):
    if CONTEXT_TITLE in request.POST:
        return request.POST[CONTEXT_TITLE]

    if CONTEXT_TITLE in request.session:
        return request.session[CONTEXT_TITLE]


def get_context_id(request):
    if CONTEXT_ID in request.POST:
        return request.POST[CONTEXT_ID]

    if CONTEXT_ID in request.session:
        return request.session[CONTEXT_ID]


def get_context_title(request):
    if CONTEXT_TITLE in request.POST:
        return request.POST[CONTEXT_TITLE]

    if CONTEXT_TITLE in request.session:
        return request.session[CONTEXT_TITLE]
    return ''


def get_context_label(request):
    if CONTEXT_LABEL in request.session:
        return request.session[CONTEXT_LABEL]
    return ''


def get_quiz_name(request):
    if QUIZ_NAME in request.session:
        return request.session[QUIZ_NAME]
    elif RESOURCE_LINK_TITLE in request.session:
        return request.session[RESOURCE_LINK_TITLE]
    return ''


def get_user_id(request):
    if USER_ID in request.session:
        return request.session[USER_ID]


def get_user_email(request):
    if USER_EMAIL in request.session:
        return request.session[USER_EMAIL]
    return ''


def get_user_name(request):
    if USER_NAME in request.session:
        return request.session[USER_NAME]
    return ''


def get_result_sourced_id(request):
    if RESULT_SOURCE_ID in request.session:
        return request.session[RESULT_SOURCE_ID]
    return ''


def get_outcome_service_url(request):
    if OUTCOME_SERVICE_URL in request.session:
        return request.session[OUTCOME_SERVICE_URL]
    return None


def get_oauth_consumer_key(request):
    if OAUTH_CONSUMER_KEY in request.session:
        return request.session[OAUTH_CONSUMER_KEY]

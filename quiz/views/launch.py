from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from quiz.utils import lti
import quiz.utils.lti_validator as lti_validator
from . import manager
from . import student


@csrf_exempt
def index(request):
    """
    The function is the entry point, it validates the POST request (if any) as LTI
    compliant, and then return the appropriate view to the user.
    """
    if request.method == "POST":
        valid = lti_validator.validate_request(request)
        if valid:      
            lti.save_launch_request_session(request)  # Save the Launch Request Parameters to the session
            if lti.is_student(request):
                return student.index(request)
            elif lti.is_manager(request):
                return manager.index(request)
        return render(request, "error.html")  # If NOT valid, or role is neither student nor manager
    else:
        # it is not a POST (LTI) request, launch home page.
        return render(request, 'home.html')
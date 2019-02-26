from django.db import models
from ..models import Quiz, LTIUser, Response


class OutcomeServiceData(models.Model):
    """
    Stores the lis_result_sourcedid for each resource_link_id/user_id 
    pair (i.e., Quiz and LTIUser pair)
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    user = models.ForeignKey(LTIUser, on_delete=models.CASCADE)
    lis_result_sourcedid = models.CharField(null=True, max_length=200, help_text="lis_result_sourcedid")
    # saves the Response whose grade was last successfully sent
    response_sent = models.ForeignKey(Response, on_delete=models.DO_NOTHING, null=True)
    outcome_send_time = models.DateTimeField(null=True)

    # TODO: Check if the following attribute is correct/needed.
    # lis_outcome_service_url should be same for all users of one consumer, but it isn't!!
    # Thus adding this for each user. I don't think it should be stored per user as it is redundant?
    lis_outcome_service_url = models.TextField(help_text="lis_outcome_service_url ", null=True)
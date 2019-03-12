from django.db import models
from django.utils import timezone
from ..models import *
import json


class Answer (models.Model):
    """
    Stores the time spent by the student to give response per question per attempt (response).
    It only contains those questions which are viewed by the student during the attempt,
    # TODO: We can add the actual answer / option id of the student in this model (?)
    """
    response = models.ForeignKey(Response,  on_delete=models.CASCADE)   # the response we are dealing with
    question = models.ForeignKey(Question, on_delete=models.CASCADE)    # the question for which the response is to be saved
    answer = models.TextField(blank = True, null=True)                  # Initialize the response as empty dictionary
    time_spent = models.PositiveIntegerField(blank=True, default= 0, help_text='Store the time spent by the \
        on the `question` in this `response`')


    @staticmethod
    def add_time_spent(response, question, time_duration):
        """
        Searche for the response and question tuple if exists, else create it and add the give time_duration
        to the time_spent. 

        # TODO: Make sure that such sanity checking is actually required, or we can do something
        The function should also does the sanity check by making sure that time_duration is not larger than 
        the time for which the quiz has been live. We are doing this because if a user/application messes up
        and sends invalid time_duration which are very large, then that will spoil the average time taken and
        everything else. 
        """
        answer, success = Answer.objects.get_or_create(response=response, question=question)
        # basic sanity checking
        max_duration = (datetime.datetime.utcnow() - response.start_time).total_seconds()     # any time_duration cannot be longer than the time which has passed since starting the attempt
        if time_duration <= max_duration:
            answer.time_spent += time_duration
            answer.save()
            return True
        return False

    @staticmethod
    def set_answer(response, question, answer):
        """
        Function to set the answer for the question in this attempt
        """
        # TODO: Yet to be implemented.
        pass


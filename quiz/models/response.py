from django.db import models
from django.utils import timezone
from ..models import *
import datetime
import json


class Response(models.Model):
    quiz = models.ForeignKey(Quiz,  on_delete=models.CASCADE)
    user = models.ForeignKey(LTIUser,  on_delete=models.CASCADE)
    question_ids = models.JSONField(default=list, help_text="Stores the order of questions to be shown to student")
    attempt_number = models.IntegerField(null=True)
    response = models.TextField(blank = True, default = '{}') #Initialize the response as empty dictionary
    questions_start_time = models.JSONField(default=dict, help_text="Stores the start time of each question")
    ip_address = models.CharField(max_length=50, default="0.0.0.0")
    start_time = models.DateTimeField(default = datetime.datetime.utcnow)
    end_time = models.DateTimeField(null=True)
    tab_switch_count = models.JSONField(default=dict)
    submission_time = models.DateTimeField(null=True)
    submitted = models.BooleanField(default= False)
    events = models.JSONField(default={})

    def __str__(self):
        return f"User {self.user}'s Response"

    def add_or_update_response(self, qid, newResponse, events):
        response = json.loads(self.response)
        if response == '' or type(response) != dict:
            response = {}
        responseList = response.get(qid,[])
        responseList.append(( newResponse, timezone.now().timestamp() ))
        self.events[qid] = self.events.get(qid, [])
        self.events[qid].append(events)
        response[qid] = responseList
        self.response = json.dumps(response)
        self.save()

    def get_response(self, qid=None):
        """
        Returns the response for the given qid if provided, else the complete response
        is returned.
        """
        response = json.loads(self.response)
        if not qid:
            return response
        qid = str(qid) #convert qid to string for the sake of json
        if qid in response:
            return response[qid][-1][0]
        else:
            return None

    def clear_response(self, qid):
        """
        Clears the response for the given id by removing the corresponding qid from the response.response.
        Returns True if the response existed, and is deleted. False if the response didn't exist.
        """
        response_dict = json.loads(self.response)
        qid = str(qid)
        if qid in response_dict:
            del response_dict[qid]
            self.response = json.dumps(response_dict)
            self.save()
            return True
        return False


    def set_end_time(self):
        quizTime = QuizSettings.objects.get(quiz = self.quiz).duration
        if quizTime:
                self.end_time = self.start_time + datetime.timedelta(minutes=quizTime)
        self.save()

    def save(self, *args, **kwargs):
        if not self.quiz or not self.user:
            raise Exception("Quiz and User must be passed to create response object")
        super().save(*args, **kwargs)


    class Meta:
        get_latest_by = "start_time"


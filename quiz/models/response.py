from django.db import models
from django.utils import timezone
from ..models import *
import datetime
import json


class Response(models.Model):
    quiz = models.ForeignKey(Quiz,  on_delete=models.CASCADE)
    user = models.ForeignKey(LTIUser,  on_delete=models.CASCADE)
    attempt_number = models.IntegerField(null=True)
    response = models.TextField(blank = True, default = '{}') #Initialize the response as empty dictionary
    start_time = models.DateTimeField(default = datetime.datetime.utcnow)
    end_time = models.DateTimeField(null=True)
    submission_time = models.DateTimeField(null=True)
    submitted = models.BooleanField(default= False)

    def add_or_update_response(self, qid, newResponse):
        response = json.loads(self.response)
        if response == '' or type(response) != dict:
            response = {}
        response[qid] = newResponse
        self.response = json.dumps(response)
        self.save()

    def get_response(self, qid=None):
        '''
        Returns the response for the given qid if provided, else the complete response
        is returned.
        '''
        response = json.loads(self.response)
        if not qid:
            return response
        qid = str(qid) #convert qid to string for the sake of json
        if qid in response:
            return response[qid]
        else:
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


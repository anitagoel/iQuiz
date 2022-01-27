from django.db import models
from django.utils import timezone
import datetime
#from django.core.validators import MinValueValidator, MaxValueValidator
from .lti_user import *
from . import custom_fields as custom_fields


class Quiz(models.Model):
    """
    The Quiz Model is used to store the basic information about the quiz.
    The Primary Key (auto generated) will be used as Quiz Id.
    """
    consumer_key = models.CharField(max_length=100, help_text='Used to store LTI consumer key')
    resourceLinkId = models.CharField(max_length=100, help_text = "Resource_link_id")
    contextId = models.CharField(
        max_length=200,
        help_text="Context Id: Unique for each term (run) of the course"
    )
    contextTitle = models.CharField(max_length=100, help_text="Course Name of the quiz in the platform")
    createdOn = models.DateTimeField(default=datetime.datetime.utcnow)
    updatedOn = models.DateTimeField(auto_now=True)
    quizName = models.CharField(max_length=100, blank=True)
    published = models.BooleanField(default=False)
    isEverAttempted = models.BooleanField(
        default=False,
        help_text="Set to True if the Quiz has been attempted by at least one student"
    )

    def save(self, *args, **kwargs):
        self.updatedOn = datetime.datetime.utcnow()
        super().save(*args, **kwargs)
        
    def __str__(self):
        if (self.quizName != ''):
            return self.quizName
        return str(self.contextId) + " : " + str(self.createdOn)

    class Meta:
        get_latest_by = "createdOn"



class QuizSettings(models.Model):
    """
    The class to store the Settings of a Quiz
    """
    quiz = models.OneToOneField(Quiz, on_delete = models.CASCADE, primary_key=True)
    randomizeQuestionOrder = models.BooleanField(default=False, verbose_name="Randomize Question Order")
    deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Deadline",
        help_text="Set the deadline for the Quiz. Leave blank if not required"
    )
    # NULL value of duration means unlimited time
    duration = custom_fields.IntegerRangeField(
        default=30,
        null=True,
        verbose_name="Duration",
        min_value=1,
        blank=True,
        help_text="Set the duration of quiz in minutes. Leave blank if timer is not required")

    timeBetweenAttempt = custom_fields.IntegerRangeField(
        default=0, null=True,
        verbose_name="Time Between Attempts",
        min_value=0,
        help_text="Set the time between the two consecutive attempts."
    )
    maxAttempts = custom_fields.IntegerRangeField(
        blank=True,
        null=True,
        verbose_name="Maximum Attempts",
        help_text="Set the maximum number of allowed attempts. Leave blank for unlimited attempts."
    )
    graded = models.BooleanField(
        default = True,
        verbose_name="Graded",
        help_text="Set whether the quiz is graded"
    )
    information = models.TextField(
        default='',
        verbose_name="Information",
        help_text="Set the information that will be shown to the student on the quiz page.\
         This will be shown in a html modal on clicking the button 'Information'. Leave blank to hide the button."
    )
    # TODO: showAnswers = models.ChoiceField() ##To be implemented
    showAnswersAfterAttempt = models.BooleanField(
        default=True,
        verbose_name="Show Answers After Attempt",
        help_text="Show correct answers to students after the attempt."
        )

    def __str__(self):
        if self.quiz.quizName != '':
            return self.quiz.quizName
        return str(self.quiz.contextId) + " : " + str(self.quiz.createdOn)

    def save(self, *args, **kwargs):
        if self.deadline =='':
            self.deadline = None
        if self.duration == '':
            self.duration = None
        if self.maxAttempts == '':
            self.maxAttempts = None

        super().save(*args, **kwargs)


class QuizManager(models.Model):
    """
    The QuizManager model is used to store the details of the manager of the quiz.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    manager = models.ForeignKey(LTIUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.manager.name
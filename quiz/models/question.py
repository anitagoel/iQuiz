from ..models import *
from django.db import models


class Difficulty(models.TextChoices):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class Question(models.Model):
    """
    Model to store questions for the Quizzes.
    It stores all the questions.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_type = models.CharField(max_length = 100, null=True)
    video_file = models.FileField(upload_to='vmcq/', null=True, blank=True)
    question_weight = models.DecimalField(decimal_places = 2, max_digits = 5, default = 1)
    question_difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.LOW)
    serial_number = models.PositiveIntegerField(default = 1, verbose_name="Serial Number")
    draft_statement = models.TextField(default='', null=True)
    draft_options_data = models.TextField(null=True)
    draft_expected_response = models.TextField(null=True)
    draft_other_data = models.TextField(null=True)  # can be used to store any data which the question wants/needs
    statement = models.TextField(null=True, blank=True) 
    options_data = models.TextField(null=True)
    expected_response = models.TextField(null=True)
    other_data = models.TextField(null=True)
    published = models.BooleanField(default = False, blank=True)
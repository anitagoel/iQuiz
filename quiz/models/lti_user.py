from django.db import models

class LTIUser(models.Model):
    """
    The class is used to store the data about the user_id, name, and email.
    """
    userId = models.CharField(max_length=200, help_text="User ID as in the LTI Launch Request")
    name = models.CharField(null=True, max_length = 100, blank=True, help_text="Name of the user if available/given.")
    email = models.CharField(null=True, max_length=100, blank=True, help_text="Email of the student if provided")
    role = models.CharField(max_length=20, blank=False, help_text="Role of the user")
    
    def __str__(self):
        if self.name and self.name != '':
            return self.name
        return self.userId

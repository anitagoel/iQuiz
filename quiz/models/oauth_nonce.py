from django.db import models


class OAuthNonce(models.Model):
    """
    Model to store the timestamps and nonce values for the client(s).
    """
    client_key = models.CharField(max_length=30)
    nonce = models.CharField(max_length=150)
    timestamp = models.DateTimeField()
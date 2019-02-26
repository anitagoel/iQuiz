from oauthlib.oauth1 import RequestValidator
from oauthlib.common import to_unicode
from django.conf import settings
from pylti.common import *

from lti.contrib.django import DjangoToolProvider
from ..models import OAuthNonce

from datetime import datetime, timedelta
NONCE_STORAGE_TIME = 5  # minutes


def validate_request(request):
    """
    Function to validate that the request is a valid LTI Launch Request.
    """
    if request is None:
        raise ValueError("Request can't be none!")
    params = request.POST.copy()
    url = request.build_absolute_uri()
    consumers = settings.LTI_OAUTH_CREDENTIALS
    valid_lti = verify_request_common(
        consumers,
        url,
        request.method,
        request.META,
        params)
    # TODO: If possible, then implement the oauth verification
    # TODO: remove DjangoToolProvider thing from here!
    '''
    print("validity of valid_lti = ", valid_lti)
    validator = ProxyValidator(LTIValidator())
    endpoint = SignatureOnlyEndpoint(validator)
    # oauth validation for nonce, timestamp etc...
    headers = dict([(k, request.META[k])
                    for k in request.META if
                    k.upper().startswith('HTTP_') or
                    k.upper().startswith('CONTENT_')])
    print(request.method)
    valid_req, request = endpoint.validate_request(
        url,
        request.method,
        to_params(params),
        headers
    )
    print("validity of valid_req = ", request)
    '''
    tool_provider = DjangoToolProvider.from_django_request(request=request)

    # the tool provider uses the 'oauthlib' library which requires an instance
    # of a validator class when doing the oauth request signature checking.
    # see https://oauthlib.readthedocs.org/en/latest/oauth1/validator.html for
    # info on how to create one
    validator = LTIValidator()
    # validate the oauth request signature
    ok = tool_provider.is_valid_request(validator)

    return valid_lti and ok


class LTIValidator(RequestValidator):
    """
    An LTI Validator class used for oauth validation.
    Inherits RequestValidator from outhlib.oauth1
    """
    enforce_ssl = False
    dummy_secret = 'NotAGoodSecretForDummyTesting'
    dummy_client = (u'dummy_'
        '2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae')

    def check_client_key(self, key):
        return len(key) > 0

    def check_nonce(self, nonce):
        """
        Check that the nonce contains no special characters.
        :param nonce:
        :return: true if nonce is valid, else false.
        """
        # TODO: Add nonce checking here.
        return len(nonce) > 0

    def validate_client_key(self, client_key, request):
        return client_key in settings.LTI_OAUTH_CREDENTIALS

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None,
                                     access_token=None):
        try:
            timestamp = float(timestamp)
        except ValueError:
            raise Exception("Timestamp from OAuth Request is not valid.")

        timestamp = datetime.fromtimestamp(timestamp)
        # Check that client_key, nonce and timestamp combination is not in the database table OAuthNonce
        failed = OAuthNonce.objects.filter(client_key=client_key, nonce=nonce, timestamp=timestamp).exists()
        if failed:
            return False
        # add the triplet to the table OAuthNonce
        oauth_nonce = OAuthNonce(client_key=client_key, nonce=nonce, timestamp=timestamp)
        oauth_nonce.save()
        # remove older nonces than the NONCE_STORAGE_TIME
        time_threshold = datetime.now() - timedelta(minutes=NONCE_STORAGE_TIME)
        very_old_oauth_nonces = OAuthNonce.objects.filter(timestamp__lt=time_threshold)
        very_old_oauth_nonces.delete()
        return True

    def get_client_secret(self, client_key, request):
        """
        Retrieves the client secret from the LTI_OAUTH_CREDENTIALS defined in the
        settings file.
        :param client_key:
        :param request:
        :return: string: client secret.
        """
        consumer = settings.LTI_OAUTH_CREDENTIALS.get(client_key, dict())
        if consumer and 'secret' in consumer:
            secret = consumer['secret']
        else:
            secret = self.dummy_secret
        # make sure secret val is unicode
        return to_unicode(secret)



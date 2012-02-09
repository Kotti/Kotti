import hashlib
import time
import urllib

from pyramid_mailer.message import Message
from pyramid_mailer.mailer import Mailer

from kotti import get_settings


SET_PASSWORD_SUBJECT = u"Your registration for %(site_title)s"
SET_PASSWORD_BODY = u"""Hello, %(user_title)s!

You've just been invited to join %(site_title)s.  Click here to set
your password and log in: %(url)s
"""

RESET_PASSWORD_SUBJECT = u"Reset your password for %(site_title)s"
RESET_PASSWORD_BODY = u"""Hello, %(user_title)s!

Click this link to reset your password at %(site_title)s: %(url)s
"""

message_templates = {
    'set-password': dict(
        subject=SET_PASSWORD_SUBJECT, body=SET_PASSWORD_BODY),
    'reset-password': dict(
        subject=RESET_PASSWORD_SUBJECT, body=RESET_PASSWORD_BODY),
    }

_inject_mailer = []
def get_mailer():
    # Consider that we may have persistent settings
    if _inject_mailer:
        return _inject_mailer[0]
    return Mailer.from_settings(get_settings()) # pragma: no cover

def make_token(user, seconds=None):
    secret = get_settings()['kotti.secret2']
    if seconds is None:
        seconds = time.time()
    token = '%s:%s:%s' % (user.name, secret, seconds)
    return '%s:%s' % (hashlib.sha224(token).hexdigest(), seconds)

def validate_token(user, token, valid_hrs=24):
    """
      >>> from kotti.testing import setUp, tearDown
      >>> ignore = setUp()
      >>> class User(object):
      ...     pass
      >>> daniel = User()
      >>> daniel.name = u'daniel'
      >>> alice = User()
      >>> alice.name = u'alice'
      >>> token = make_token(daniel)
      >>> validate_token(daniel, token)
      True
      >>> validate_token(alice, token)
      False
      >>> validate_token(daniel, 'foo')
      False
      >>> token = make_token(daniel, seconds=time.time() - 100000)
      >>> validate_token(daniel, token)
      False
      >>> validate_token(daniel, token, valid_hrs=48)
      True
      >>> tearDown()
    """
    try:
        seconds = float(token.split(':')[1])
    except (IndexError, ValueError):
        return False
    if token == make_token(user, seconds):
        if time.time() - seconds < 60 * 60 * valid_hrs:
            return True
    return False

def send_set_password(user, request, templates='set-password', add_query=None):
    site_title = get_settings()['kotti.site_title']
    token = make_token(user)
    user.confirm_token = unicode(token)
    set_password_query = {'token': token, 'email': user.email}
    if add_query:
        set_password_query.update(add_query)
    url = '%s/@@set-password?%s' % (
        request.application_url,
        urllib.urlencode(set_password_query),
        )
    variables = dict(
        user_title=user.title,
        site_title=site_title,
        url=url,
        )

    if isinstance(templates, str):
        templates = message_templates[templates]
    message = Message(
        recipients=[u'"%s" <%s>' % (user.title, user.email)], # XXX naive?
        subject=templates['subject'] % variables,
        body=templates['body'] % variables,
        )
    mailer = get_mailer()
    mailer.send(message)

import hashlib
import time
import urllib

from html2text import HTML2Text
from pyramid.renderers import render
from pyramid_mailer.mailer import Mailer
from pyramid_mailer.message import Message

from kotti import get_settings


SET_PASSWORD_SUBJECT = u"Your registration for %(site_title)s"
SET_PASSWORD_BODY = u"""Hello, %(user_title)s!

You've just been invited to join %(site_title)s.  Click here to set
your password and log in: %(url)s.
"""

RESET_PASSWORD_SUBJECT = u"Reset your password for %(site_title)s."
RESET_PASSWORD_BODY = u"""Hello, %(user_title)s!

Click this link to reset your password at %(site_title)s: %(url)s.
"""

_inject_mailer = []


def get_mailer():
    # Consider that we may have persistent settings
    if _inject_mailer:
        return _inject_mailer[0]
    return Mailer.from_settings(get_settings())  # pragma: no cover


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


def send_email(request, recipients, template_name, template_vars={}):
    """ General email sender.

    :param request: current request.
    :type request: :class:`kotti.request.Request`

    :param recipients: list of email addresses. Each email should be a
                       string like: u'"John Doe" <joedoe@foo.com>'.
    :type recipients: list

    :param template_name: asset specification (e.g.
                          'mypackage:templates/email.pt')
    :type template_name: string

    :param template_vars: set of variables present on template.
    :type template_vars: dict
    """

    text = render(template_name, template_vars, request)
    subject, htmlbody = text.strip().split('\n', 1)
    subject = subject.replace('Subject:', '', 1).strip()
    html2text = HTML2Text()
    html2text.body_width = 0
    textbody = html2text.handle(htmlbody).strip()

    message = Message(
        recipients=recipients,
        subject=subject,
        body=textbody,
        html=htmlbody,
        )
    mailer = get_mailer()
    mailer.send(message)


def email_set_password(user, request,
                       template_name='kotti:templates/email-set-password.pt',
                       add_query=None):
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
    recipients = [u'"%s" <%s>' % (user.title, user.email)]  # XXX naive?
    send_email(request, recipients, template_name, variables)

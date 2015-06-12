# -*- coding: utf-8 -*-

from mock import patch
from pytest import raises

from kotti.testing import Dummy
from kotti.testing import DummyRequest


# filter deprecation warnings for code that is still tested...
from warnings import filterwarnings
filterwarnings('ignore', '^send_set_password is deprecated')


class TestSendEmail:
    def setup_method(self, method):
        get_mailer_patcher = patch('kotti.message.get_mailer')
        get_mailer = get_mailer_patcher.start()
        self.mailer = get_mailer.return_value

        self.patchers = (get_mailer_patcher, )

    def teardown_method(self, method):
        for patcher in self.patchers:
            patcher.stop()

    def test_send_email(self, dummy_request):
        from kotti.message import send_email

        send_email(dummy_request,
                   [u'"John Doe" <joedoe@foo.com>'],
                   'kotti:templates/email-reset-password.pt',
                   {'site_title': u'My site',
                    'user_title': u'John Doe',
                    'url': u'http://foo.com'}
                   )

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert [u'"John Doe" <joedoe@foo.com>'] == message.recipients
        assert 'Reset your password' in message.subject

    def test_send_email_without_template_vars(self, dummy_request):
        from kotti.message import send_email
        with raises(NameError):
            send_email(dummy_request,
                       [u'"John Doe" <joedoe@foo.com>'],
                       'kotti:templates/email-reset-password.pt')


class TestSendSetPassword:
    def setup_method(self, method):
        get_settings_patcher = patch('kotti.message.get_settings')
        self.get_settings = get_settings_patcher.start()
        self.get_settings.return_value = {
            'kotti.site_title': 'Awesome site',
            'kotti.secret2': '123',
            }

        get_mailer_patcher = patch('kotti.message.get_mailer')
        get_mailer = get_mailer_patcher.start()
        self.mailer = get_mailer.return_value

        self.patchers = (get_settings_patcher, get_mailer_patcher)

    def teardown_method(self, method):
        for patcher in self.patchers:
            patcher.stop()

    def test_email_set_password_basic(self, db_session):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(user, DummyRequest())

        assert hasattr(user, 'confirm_token')
        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'Your registration' in message.subject
        assert 'Joe' in message.body
        assert 'Awesome site' in message.body

    def test_email_set_password_add_query(self, db_session):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(
            user, DummyRequest(), add_query={'another': 'param'})

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'another=param' in message.body


class TestEmailSetPassword:
    def setup_method(self, method):
        get_settings_patcher = patch('kotti.message.get_settings')
        self.get_settings = get_settings_patcher.start()
        self.get_settings.return_value = {
            'kotti.site_title': 'Awesome site',
            'kotti.secret2': '123',
            }

        get_mailer_patcher = patch('kotti.message.get_mailer')
        get_mailer = get_mailer_patcher.start()
        self.mailer = get_mailer.return_value

        self.patchers = (get_settings_patcher, get_mailer_patcher)

    def teardown_method(self, method):
        for patcher in self.patchers:
            patcher.stop()

    def test_email_set_password_basic(self, db_session):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(user, DummyRequest())

        assert hasattr(user, 'confirm_token')
        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert message.subject.startswith('Your registration')
        assert 'Joe' in message.body
        assert 'Joe' in message.html
        assert '<p' not in message.body
        assert '<p' in message.html
        assert 'Awesome site' in message.body

    def test_email_set_password_other_template(self, db_session):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(
            user, DummyRequest(),
            template_name='kotti:templates/email-reset-password.pt')

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert message.subject.startswith('Reset your password')

    def test_email_set_password_add_query(self, db_session):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(
            user, DummyRequest(), add_query={'another': 'param'})

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'another=param' in message.body

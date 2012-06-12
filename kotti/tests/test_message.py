from mock import patch

from kotti.testing import Dummy
from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase


class TestSendSetPassword(UnitTestBase):
    def setUp(self):
        super(TestSendSetPassword, self).setUp()

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

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_email_set_password_basic(self):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(user, DummyRequest())

        assert hasattr(user, 'confirm_token')
        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'Your registration' in message.subject
        assert 'Joe' in message.body
        assert 'Awesome site' in message.body

    def test_send_set_password_other_template(self):
        from kotti.message import send_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        send_set_password(user, DummyRequest(), templates='reset-password')

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'Reset your password' in message.subject

    def test_send_set_password_other_template_entirely(self):
        from kotti.message import send_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        send_set_password(user, DummyRequest(), templates=dict(
            subject=u"Hey there %(user_title)s",
            body=u"This is %(site_title)s speaking",
            ))

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert message.subject == 'Hey there Joe'
        assert message.body == 'This is Awesome site speaking'

    def test_email_set_password_add_query(self):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(
            user, DummyRequest(), add_query={'another': 'param'})

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'another=param' in message.body

    def test_send_set_password_add_query(self):
        from kotti.message import send_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        send_set_password(user, DummyRequest(), add_query={'another': 'param'})

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'another=param' in message.body


class TestEmailSetPassword(UnitTestBase):
    def setUp(self):
        super(TestEmailSetPassword, self).setUp()

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

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_email_set_password_basic(self):
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

    def test_email_set_password_other_template(self):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(
            user, DummyRequest(),
            template_name='kotti:templates/email-reset-password.pt')

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert message.subject.startswith('Reset your password')

    def test_email_set_password_add_query(self):
        from kotti.message import email_set_password

        user = Dummy(name=u'joe', email='joe@bar.com', title=u'Joe')
        email_set_password(
            user, DummyRequest(), add_query={'another': 'param'})

        assert self.mailer.send.called
        message = self.mailer.send.call_args[0][0]
        assert 'another=param' in message.body

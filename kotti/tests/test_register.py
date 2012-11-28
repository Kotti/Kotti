from kotti.testing import DummyRequest
from mock import patch
from mock import call


class TestRegister:

    def test_register_form(self, db_session):
        from kotti.resources import get_root
        from kotti.views.login import register

        root = get_root()
        request = DummyRequest()
        res = register(root, request)
        assert(res['form'][:5] == '<form')

    def test_register_submit_empty(self, db_session):
        from kotti.resources import get_root
        from kotti.views.login import register

        root = get_root()
        request = DummyRequest()
        request.POST['register'] = u'register'
        res = register(root, request)
        assert 'There was a problem with your submission' in res['form']

    def test_register_submit(self, db_session):
        from kotti.resources import get_root
        from kotti.views.login import register
        from pyramid.httpexceptions import HTTPFound

        root = get_root()
        request = DummyRequest()
        request.POST['title'] = u'Test User'
        request.POST['name'] = u'test'
        request.POST['email'] = u'test@example.com'
        request.POST['register'] = u'register',

        with patch('kotti.views.login.UserAddFormView') as form:
            with patch('kotti.views.login.get_principals') as getp:
                res = register(root, request)
                form.assert_has_calls([call().add_user_success({
                    'name': u'test',
                    'roles': u'',
                    'title': u'Test User',
                    'send_email': True,
                    'groups': u'',
                    'email': u'test@example.com'})]
                )
        assert(isinstance(res, HTTPFound))

    def test_register_event(self, db_session):
        from kotti.resources import get_root
        from kotti.views.login import register
        from kotti.views.login import UserSelfRegistered
        root = get_root()
        request = DummyRequest()
        request.POST['title'] = u'Test User'
        request.POST['name'] = u'test'
        request.POST['email'] = u'test@example.com'
        request.POST['register'] = u'register',

        with patch('kotti.views.login.UserAddFormView') as form:
            with patch('kotti.views.login.get_principals') as getp:
                with patch('kotti.views.login.notify') as notify:
                    res = register(root, request)
        assert(notify.call_count == 1)

    def test_register_submit_groups_and_roles(self, db_session):
        from kotti.resources import get_root
        from kotti.views.login import register
        from pyramid.httpexceptions import HTTPFound

        root = get_root()
        request = DummyRequest()
        request.POST['title'] = u'Test User'
        request.POST['name'] = u'test'
        request.POST['email'] = u'test@example.com'
        request.POST['register'] = u'register',

        with patch('kotti.views.login.UserAddFormView') as form:
            with patch('kotti.views.login.get_principals') as getp:
                with patch('kotti.views.login.get_settings') as get_settings:
                    get_settings.return_value = {
                        'kotti.register.group': 'mygroup',
                        'kotti.register.role': 'myrole',
                        }

                    res = register(root, request)

        form.assert_has_calls([
            call().add_user_success({
                'name': u'test',
                'roles': set([u'role:myrole']),
                'title': u'Test User',
                'send_email': True,
                'groups': [u'mygroup'],
                'email': u'test@example.com',
                })])
        assert(isinstance(res, HTTPFound))


class TestNotRegister:
    def test_it(self, app):
        res = app.post('/register', status=404)
        assert res.status == '404 Not Found'

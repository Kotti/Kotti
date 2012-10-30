# -*- coding: utf-8 -*-

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
        request.POST['register'] = 'register'
        res = register(root, request)
        assert(res['form'].find('There was a problem with your submission') > 0)

    def test_register_submit(self, db_session):
        from kotti.resources import get_root
        from kotti.views.login import register
        from pyramid.httpexceptions import HTTPFound

        root = get_root()
        request = DummyRequest()
        request.POST['title'] = 'Test User'
        request.POST['name'] = 'test'
        request.POST['email'] = 'test@example.com'
        request.POST['register'] = 'register',

        with patch('kotti.views.login.UserAddFormView') as form:
            res = register(root, request)
            form.assert_has_calls([call().add_user_success({
                'name': u'test',
                'roles': '',
                'title': u'Test User',
                'send_email': True,
                'groups': '',
                'email': u'test@example.com'})]
            )
        assert(isinstance(res, HTTPFound))

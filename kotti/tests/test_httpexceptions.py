# -*- coding: utf-8 -*-
""" Kotti HTTP Exception browser tests """

import pytest


def test_404_anon(webtest, root):

    resp = webtest.app.get('/non-existent', status=404)
    assert 'Not Found' in resp.text


@pytest.mark.user('admin')
def test_404_anon(webtest, root):

    resp = webtest.app.get('/non-existent', status=404)
    assert 'Not Found' in resp.text


def test_404_api_root(db_session, dummy_request):
    from kotti.resources import get_root
    from kotti.views.util import TemplateAPI
    from pyramid.httpexceptions import HTTPNotFound

    api = TemplateAPI(HTTPNotFound(), dummy_request)

    assert api.root == get_root()

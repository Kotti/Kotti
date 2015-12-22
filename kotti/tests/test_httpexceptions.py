""" Kotti HTTP Exception browser tests """

import pytest


def test_404_anon(webtest, root):

    resp = webtest.app.get('/non-existent', status=404)
    assert 'Not Found' in resp.text


@pytest.mark.user('admin')
def test_404_anon(webtest, root):

    resp = webtest.app.get('/non-existent', status=404)
    assert 'Not Found' in resp.text

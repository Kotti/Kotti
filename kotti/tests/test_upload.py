# -*- coding: utf-8 -*-

import json

from kotti.testing import BASE_URL
from kotti.testing import user
from kotti.views.edit.upload import UploadView
from pytest import raises
from zope.testbrowser.browser import LinkNotFoundError


def test_upload_anonymous(root, dummy_request, browser):

    view = UploadView(root, dummy_request)

    assert view.factories == []

    link = browser.getLink

    browser.open(u'{0}/'.format(BASE_URL))

    # There must be no Upload Link for anonymous users
    with raises(LinkNotFoundError):
        link('Upload Content').click()

    # Upload views must redirect to login for anonymous users
    browser.open(u'{0}/upload'.format(BASE_URL))
    assert browser.url.startswith(u'{0}/@@login'.format(BASE_URL))

    browser.open(u'{0}/content_types'.format(BASE_URL))
    assert browser.url.startswith(u'{0}/@@login'.format(BASE_URL))


@user('admin')
def test_upload_authenticated_wo_mimetype(root, dummy_request, browser):

    # cannot call content_types without mimetype
    with raises(KeyError):
        browser.open(u'{0}/content_types'.format(BASE_URL))


@user('admin')
def test_upload_authenticated_text(root, dummy_request, browser):

    # get possible content types for text/plain
    browser.open(u'{0}/content_types?mimetype=text/plain'.format(BASE_URL))
    j = json.loads(browser.contents)
    assert 'content_types' in j

    # only files are allowed
    types = j['content_types']
    assert len(types) == 1
    assert types[0]['name'] == u'File'

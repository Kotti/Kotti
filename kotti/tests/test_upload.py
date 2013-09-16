# -*- coding: utf-8 -*-

import json

from mechanize._mechanize import LinkNotFoundError
from pytest import raises

from kotti.testing import BASE_URL
from kotti.testing import user
from kotti.views.edit.upload import UploadView


def test_upload_anonymous(root, dummy_request, browser):

    view = UploadView(root, dummy_request)

    assert view.factories == []

    link = browser.getLink

    browser.open('%s/' % BASE_URL)

    # There must be no Upload Link for anonymous users
    with raises(LinkNotFoundError):
        link('Upload Content').click()

    # Upload views must redirect to login for anonymous users
    browser.open('%s/upload' % BASE_URL)
    assert browser.url.startswith('%s/@@login' % BASE_URL)

    browser.open('%s/content_types' % BASE_URL)
    assert browser.url.startswith('%s/@@login' % BASE_URL)

    # import pdb; pdb.set_trace()


@user('admin')
def test_upload_authenticated_wo_mimetype(root, dummy_request, browser):

    # cannot call content_types without mimetype
    with raises(KeyError):
        browser.open('%s/content_types' % BASE_URL)


@user('admin')
def test_upload_authenticated_text(root, dummy_request, browser):

    # get possible content types for text/plain
    browser.open('%s/content_types?mimetype=text/plain' % BASE_URL)
    j = json.loads(browser.contents)
    assert 'content_types' in j

    # only files are allowed
    types = j['content_types']
    assert len(types) == 1
    assert types[0]['name'] == u'File'


@user('admin')
def test_upload_authenticated_image(root, dummy_request, browser):

    link = browser.getLink

    # get possible content types for image/png
    browser.open('%s/content_types?mimetype=image/png' % BASE_URL)
    j = json.loads(browser.contents)
    assert 'content_types' in j

    # images and files are allowed
    types = j['content_types']
    assert len(types) == 2

    # images must be first
    assert types[0]['name'] == u'Image'
    assert types[1]['name'] == u'File'

    # Open the upload 'form'
    browser.open('%s/' % BASE_URL)
    link('Upload Content').click()
    assert 'Select file(s) to upload' in browser.contents

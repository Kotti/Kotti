import json

from pytest import raises
from zope.testbrowser.browser import LinkNotFoundError

from kotti.testing import BASE_URL
from kotti.testing import user
from kotti.views.edit.upload import UploadView


def test_upload_anonymous(root, dummy_request, browser):

    view = UploadView(root, dummy_request)

    assert view.factories == []

    link = browser.getLink

    browser.open(f"{BASE_URL}/")

    # There must be no Upload Link for anonymous users
    with raises(LinkNotFoundError):
        link("Upload Content").click()

    # Upload views must redirect to login for anonymous users
    browser.open(f"{BASE_URL}/upload")
    assert browser.url.startswith(f"{BASE_URL}/@@login")

    browser.open(f"{BASE_URL}/content_types")
    assert browser.url.startswith(f"{BASE_URL}/@@login")


@user("admin")
def test_upload_authenticated_wo_mimetype(root, dummy_request, browser):

    # cannot call content_types without mimetype
    with raises(KeyError):
        browser.open(f"{BASE_URL}/content_types")


@user("admin")
def test_upload_authenticated_text(root, dummy_request, browser):

    # get possible content types for text/plain
    browser.open(f"{BASE_URL}/content_types?mimetype=text/plain")
    c = browser.contents
    if isinstance(c, bytes):
        c = c.decode()
    j = json.loads(c)
    assert "content_types" in j

    # only files are allowed
    types = j["content_types"]
    assert len(types) == 1
    assert types[0]["name"] == "File"

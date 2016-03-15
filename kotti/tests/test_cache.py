# -*- coding: utf-8 -*-
import datetime
import time

from mock import patch
from mock import MagicMock
import pytest

from kotti.resources import File
from kotti.resources import Image
from kotti.testing import asset
from kotti.testing import Dummy
from kotti.views.cache import set_max_age


def parse_expires(date_string):
    return datetime.datetime(*(
        time.strptime(date_string, "%a, %d %b %Y %H:%M:%S GMT")[0:6]))


def delta(date_string):
    now = datetime.datetime.utcnow()
    return parse_expires(date_string) - now


@pytest.fixture
def cachetest_content(root, filedepot):
    image = asset('sendeschluss.jpg')
    root['textfile'] = File("file contents", u"mytext.txt", u"text/plain")
    root['image'] = Image(image.read(), u"sendeschluss.jpg", u"image/jpeg")


class TestSetMaxAge:
    def test_preserve_existing_headers(self):
        response = Dummy(headers={
            "cache-control": "max-age=17,s-max-age=42,foo,bar=42"})
        delta = datetime.timedelta(days=1)
        set_max_age(response, delta)

        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == (
            "bar=42,foo,max-age=86400,s-max-age=42")


class TestSetCacheHeaders:
    def test_caching_policy_chooser(self):
        from kotti.views.cache import set_cache_headers

        with patch('kotti.views.cache.caching_policy_chooser') as chooser:
            chooser.return_value = 'Random policy'

            event = MagicMock()
            event.response.headers.get.return_value = None

            with pytest.raises(KeyError):
                set_cache_headers(event)

        chooser.assert_called_with(
            event.request.context, event.request, event.response)

    def test_caching_policy_chooser_raises(self):
        from kotti.views.cache import set_cache_headers

        def raiser(*args, **kw):
            raise Exception()

        with patch('kotti.views.cache.caching_policy_chooser') as chooser:
            chooser.side_effect = raiser

            event = MagicMock()
            event.response.headers.get.return_value = None

            with patch('kotti.views.cache.logger'):
                set_cache_headers(event)

        chooser.assert_called_with(
            event.request.context, event.request, event.response)

    def test_header_set_before(self):
        from kotti.views.cache import CACHE_POLICY_HEADER
        from kotti.views.cache import set_cache_headers

        event = MagicMock()
        event.response.headers = {CACHE_POLICY_HEADER: 'Random policy'}

        with patch('kotti.views.cache.caching_policy_chooser') as chooser:
            with pytest.raises(KeyError):
                set_cache_headers(event)

        assert chooser.call_count == 0

    def test_request_has_no_context(self):
        from kotti.views.cache import set_cache_headers

        with patch('kotti.views.cache.caching_policy_chooser') as chooser:
            event = MagicMock()
            event.request = {}
            set_cache_headers(event)

            assert chooser.call_count == 0


class TestBrowser:

    def test_cache_unauth(self, webtest, cachetest_content):

        # html
        resp = webtest.app.get('/')
        assert resp.headers.get('X-Caching-Policy') == 'Cache HTML'
        assert resp.headers.get('Cache-Control') == 'max-age=0,s-maxage=3600'
        d = delta(resp.headers.get('Expires'))
        assert (d.days, d.seconds) < (0, 0)

        # resources
        resp = webtest.app.get('/static-kotti/base.css')
        assert resp.headers.get('X-Caching-Policy') == 'Cache Resource'
        assert resp.headers.get('Cache-Control') == 'max-age=2764800,public'
        d = delta(resp.headers.get('Expires'))
        assert (d.days, d.seconds) > (30, 0)
        assert 'Last-Modified' in resp.headers

        # post
        resp = webtest.app.post('/', '')
        assert 'X-Caching-Policy' not in resp.headers

        # 404
        resp = webtest.app.get('/this-isnt-here', status=404)
        assert 'X-Caching-Policy' not in resp.headers

        # media content
        resp = webtest.app.get('/textfile/inline-view')
        assert resp.headers.get('X-Caching-Policy') == 'Cache Media Content'
        assert resp.headers.get('Cache-Control') == 'max-age=14400,public'
        d = delta(resp.headers.get('Expires'))
        assert (d.days, d.seconds) > (0, 14000)
        resp = webtest.app.get('/image/inline-view')
        assert resp.headers.get('X-Caching-Policy') == 'Cache Media Content'
        assert resp.headers.get('Cache-Control') == 'max-age=14400,public'
        d = delta(resp.headers.get('Expires'))
        assert (d.days, d.seconds) > (0, 14000)

    @pytest.mark.user('admin')
    def test_cache_auth(self, webtest, cachetest_content):

        # html
        resp = webtest.app.get('/')
        assert resp.headers.get('X-Caching-Policy') == 'No Cache'

        # resources
        resp = webtest.app.get('/static-kotti/base.css')
        assert resp.headers.get('X-Caching-Policy') == 'Cache Resource'

        # 404
        resp = webtest.app.get('/this-isnt-here', status=404)
        assert 'X-Caching-Policy' not in resp.headers

        # media content
        resp = webtest.app.get('/textfile/inline-view')
        resp.headers.get('X-Caching-Policy') == 'No Cache'
        assert resp.headers.get('Cache-Control') == 'max-age=0,public'
        d = delta(resp.headers.get('Expires'))
        assert (d.days, d.seconds) <= (0, 0)
        resp = webtest.app.get('/image/inline-view')
        resp.headers.get('X-Caching-Policy') == 'No Cache'
        assert resp.headers.get('Cache-Control') == 'max-age=0,public'
        d = delta(resp.headers.get('Expires'))
        assert (d.days, d.seconds) <= (0, 0)

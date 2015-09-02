import datetime

from mock import patch
from mock import MagicMock
import pytest

from kotti.testing import Dummy
from kotti.views.cache import set_max_age


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

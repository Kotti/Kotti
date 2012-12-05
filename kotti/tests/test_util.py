from mock import Mock
from mock import patch


class TestRequestCache(object):

    @property
    def cache_decorator(self):
        from kotti.util import request_cache
        return request_cache

    def test_it(self, dummy_request):
        from kotti.util import clear_cache

        called = []

        @self.cache_decorator(lambda a, b: (a, b))
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        assert len(called) == 1
        my_fun(2, 1)
        assert len(called) == 2

        clear_cache()
        my_fun(1, 2)
        assert len(called) == 3

    def test_dont_cache(self, dummy_request):
        from kotti.util import DontCache
        called = []

        def dont_cache(a, b):
            raise DontCache

        @self.cache_decorator(dont_cache)
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        assert len(called) == 2


class TestLRUCache(TestRequestCache):

    @property
    def cache_decorator(self):
        from kotti.util import lru_cache
        return lru_cache


class TestTitleToName:
    def setUp(self):
        from pyramid.threadlocal import get_current_registry
        from kotti.url_normalizer import url_normalizer
        r = get_current_registry()
        settings = r.settings = {}
        settings['kotti.url_normalizer'] = [url_normalizer]
        settings['kotti.url_normalizer.map_non_ascii_characters'] = False

    def test_max_length(self):
        self.setUp()
        from kotti.util import title_to_name
        assert len(title_to_name(u'a' * 50)) == 40

    def test_normal(self):
        self.setUp()
        from kotti.util import title_to_name
        assert title_to_name(u'Foo Bar') == u'foo-bar'

    def test_disambiguate_name(self):
        from kotti.util import disambiguate_name
        assert disambiguate_name(u'foo') == u'foo-1'
        assert disambiguate_name(u'foo-3') == u'foo-4'


class TestCommand:
    def test_it(self):
        from kotti.util import command

        func = Mock()
        closer = Mock()
        with patch('kotti.util.docopt') as docopt:
            with patch('kotti.util.bootstrap') as bootstrap:
                docopt.return_value = {'<config_uri>': 'uri'}
                bootstrap.return_value = {'closer': closer}
                assert command(func, 'doc') == 0
                func.assert_called_with({'<config_uri>': 'uri'})
                docopt.assert_called_with('doc')
                bootstrap.assert_called_with('uri')
                assert closer.call_count == 1

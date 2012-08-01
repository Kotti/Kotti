from unittest import TestCase

from mock import Mock
from mock import patch
from pyramid.registry import Registry

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase


class TestRequestCache(UnitTestBase):
    def setUp(self):
        from kotti.util import request_cache

        registry = Registry('testing')
        request = DummyRequest()
        request.registry = registry
        super(TestRequestCache, self).setUp(registry=registry, request=request)
        self.cache_decorator = request_cache

    def test_it(self):
        from kotti.util import clear_cache

        called = []

        @self.cache_decorator(lambda a, b: (a, b))
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 1)
        my_fun(2, 1)
        self.assertEqual(len(called), 2)

        clear_cache()
        my_fun(1, 2)
        self.assertEqual(len(called), 3)

    def test_dont_cache(self):
        from kotti.util import DontCache
        called = []

        def dont_cache(a, b):
            raise DontCache

        @self.cache_decorator(dont_cache)
        def my_fun(a, b):
            called.append((a, b))

        my_fun(1, 2)
        my_fun(1, 2)
        self.assertEqual(len(called), 2)


class TestLRUCache(TestRequestCache):
    def setUp(self):
        from kotti.util import lru_cache

        super(TestLRUCache, self).setUp()
        self.cache_decorator = lru_cache


class TestTitleToName(TestCase):
    def test_max_length(self):
        from kotti.util import title_to_name
        assert len(title_to_name(u'a' * 50)) == 40

    def test_normal(self):
        from kotti.util import title_to_name
        assert title_to_name(u'Foo Bar') == u'foo-bar'

    def test_disambiguate_name(self):
        from kotti.util import disambiguate_name
        assert disambiguate_name(u'foo') == u'foo-1'
        assert disambiguate_name(u'foo-3') == u'foo-4'


class TestCommand(UnitTestBase):
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

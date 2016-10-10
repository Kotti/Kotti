# -*- coding: utf-8 -*-
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

    def test_max_length_40(self):
        self.setUp()
        from kotti.util import title_to_name
        assert len(title_to_name(u'a' * 50)) == 50

    def test_max_length_250(self):
        self.setUp()
        from kotti.util import title_to_name
        assert len(title_to_name(u'a' * 250)) == 240

    def test_max_length_255(self):
        self.setUp()
        from kotti.util import title_to_name
        assert len(title_to_name(u'a' * 255)) == 240

    def test_normal(self):
        self.setUp()
        from kotti.util import title_to_name
        assert title_to_name(u'Foo Bar') == u'foo-bar'

    def test_max_length_40_no_default(self):
        self.setUp()
        from kotti.util import title_to_name
        assert len(title_to_name(u'a' * 50, max_length=40)) == 40

    def test_numbering(self):
        self.setUp()
        from kotti.util import title_to_name
        assert title_to_name(u'Report Part 1',
                             blacklist=[]) == u'report-part-1'
        assert title_to_name(u'Report Part 1',
                             blacklist=['report-part-1']) == u'report-part-1-1'
        assert title_to_name(u'Report Part 3',
                             blacklist=['report-part-3']) == u'report-part-3-1'
        assert title_to_name(
            u'Report Part 3', blacklist=['report-part-3', 'report-part-3-1']
        ) == u'report-part-3-2'

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


class TestTemplateStructure:
    def test_getattr(self):
        from kotti.util import TemplateStructure

        item = TemplateStructure(u'123')
        assert item.split('2') == [u'1', u'3']


class TestLink:

    def test_link_selected(self):
        from kotti.util import Link
        from kotti.testing import DummyRequest

        req = DummyRequest()
        req.url = "http://example.com/@@manage"

        assert Link('manage').selected(Mock(__name__=None), req)

        req.url = "http://example.com/@@manage_cats"
        assert not Link('manage').selected(Mock(__name__=None), req)

    def test_link_selected_no_view_markers(self):
        from kotti.util import Link
        from kotti.testing import DummyRequest
        from mock import Mock

        req = DummyRequest()
        root = Mock(__name__=None)
        manage = Mock(__name__='manage',
                      __parent__=Mock(__name__=None))

        req.url = "http://example.com/manage"
        assert Link('manage').selected(root, req)

        req.url = "http://example.com/manage/"
        assert not Link('manage').selected(root, req)

        req.url = "http://example.com/"
        assert Link('').selected(root, req)

        req.url = "http://example.com/manage/"
        link = Link('')
        assert link.selected(manage, req)

        req.url = "http://example.com/manage"
        assert not link.selected(manage, req)

        req.url = "http://example.com/"
        assert link.selected(root, req)

        req.url = "http://example.com"
        assert link.selected(root, req)

    def test_link_target(self):
        from kotti.util import Link
        assert Link('').target is None
        assert Link('', target='_blank').target == '_blank'

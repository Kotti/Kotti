from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase


def create_contents(root=None):
    from kotti.resources import get_root
    from kotti.resources import Content, File
    if root is None:
        root = get_root()
    doc1 = root['doc1'] = Content(title=u'First Document')
    doc11 = root['doc1']['doc11'] = Content(title=u'Second Document')
    doc12 = root['doc1']['doc12'] = Content(title=u'Third Document')
    file1 = root['doc1']['file1'] = File(title=u'First File',
                                         description=u'this is a file')
    return doc1, doc11, doc12, file1


class TestSearch(UnitTestBase):

    def test_search_empty_content(self):
        from kotti.views.util import search_content
        request = DummyRequest()
        results = search_content(request, u'teststring')
        assert results == []

    def test_search_content(self):
        from kotti.views.util import search_content
        request = DummyRequest()
        doc1, doc11, doc12, file1 = create_contents()
        results = search_content(u'First Document', request)
        assert len(results) == 1
        assert results[0]['name'] == u'doc1'
        assert results[0]['title'] == u'First Document'
        results = search_content(u'Document', request)
        # The frontpage contains 'Documentation' in its body!
        assert len(results) == 4
        assert results[1]['name'] == 'doc11'
        assert results[1]['title'] == 'Second Document'
        assert results[1]['path'] == '/doc1/doc11/'
        assert results[-1]['path'] == '/'

    def test_search_file_description(self):
        from kotti.views.util import search_content
        request = DummyRequest()
        doc1, doc11, doc12, file1 = create_contents()
        results = search_content(u'this is a file', request)
        assert len(results) == 1
        assert results[0]['name'] == 'file1'
        assert results[0]['title'] == 'First File'
        assert results[0]['path'] == '/doc1/file1/'

    def test_search_content_without_permission(self):
        from kotti.views.util import search_content
        request = DummyRequest()
        create_contents()
        self.config.testing_securitypolicy(permissive=False)
        results = search_content(u'Document', request)
        assert len(results) == 0

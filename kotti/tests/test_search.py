from kotti.testing import DummyRequest


def create_contents(root):
    from kotti.resources import Content, File
    doc1 = root['doc1'] = Content(title=u'First Document')
    doc11 = root['doc1']['doc11'] = Content(title=u'Second Document')
    doc12 = root['doc1']['doc12'] = Content(title=u'Third Document')
    file1 = root['doc1']['file1'] = File(title=u'First File',
                                         description=u'this is a file')
    return doc1, doc11, doc12, file1


def create_contents_with_tags(root=None):
    from kotti.resources import get_root
    from kotti.resources import Content, File
    if root is None:
        root = get_root()

    animals = root['animals'] = Content(title=u'Animals')
    cat = root['animals']['cat'] = Content(title=u'Cat')
    dog = root['animals']['dog'] = Content(title=u'Dog')
    monkey = root['animals']['monkey'] = Content(title=u'Monkey')
    gorilla = root['animals']['gorilla'] = Content(title=u'Gorilla')
    monkey_file = root['animals']['monkey_file'] = File(
        title=u'Monkey File',
        description=u'A Rhesus Macaque and a Green Monkey walk into a bar...')

    root[u'animals'][u'cat'].tags = [u'Animals', u'Cat']
    root[u'animals'][u'dog'].tags = [u'Animals', u'Dog']
    root[u'animals'][u'monkey'].tags = [u'Animals', u'Monkey', u'Primate']
    root[u'animals'][u'monkey_file'].tags = [u'Animals', u'Monkey', u'Primate']
    root[u'animals'][u'gorilla'].tags = [u'Animals', u'Gorilla', u'Primate']

    return animals, cat, dog, monkey, gorilla, monkey_file


class TestSearch:

    def test_search_empty_content(self, db_session):
        from kotti.views.util import search_content
        request = DummyRequest()
        results = search_content(u'teststring', request)
        assert results == []

    def test_search_content(self, root):
        from kotti.views.util import search_content
        from kotti import DBSession
        from kotti.resources import Tag

        request = DummyRequest()
        doc1, doc11, doc12, file1 = create_contents(root)
        results = search_content(u'First Document', request)
        assert len(results) == 1
        assert results[0]['name'] == u'doc1'
        assert results[0]['title'] == u'First Document'
        results = search_content(u'Document', request)
        # The frontpage contains 'Documentation' in its body!
        assert len(results) == 4
        assert results[1]['name'] == u'doc11'
        assert results[1]['title'] == u'Second Document'
        assert results[1]['path'] == '/doc1/doc11/'
        assert results[1]['path'][-1] == '/'

        animals, cat, dog, \
            monkey, gorilla, monkey_file = create_contents_with_tags()

        tags = DBSession.query(Tag).all()
        assert len(tags) == 6
        results = search_content(u'Animals', request)
        assert len(results) == 6
        results = search_content(u'Cat', request)
        assert len(results) == 1
        results = search_content(u'Primate', request)
        assert len(results) == 3

        # Tags were included in general search by modifying the pre-existing
        # approach, wherein searching first worked on title and description,
        # then on body, so that the search order became:
        #
        #     first on title + description
        #         then on tags
        #             then on body
        #
        # So we test here to assure search results come back in that order.
        # Searching on 'Animals', we should find all 6 content items, and the
        # first item should be the Animals folder, found with a title hit, and
        # the other items were found via tags.
        #
        # Note: this ordering is done to have some method, but it does not
        #       necessarily constitute a specification.
        #
        results = search_content(u'Animals', request)
        assert len(results) == 6
        assert results[0]['name'] == 'animals'

    def test_search_file_description(self, root):
        from kotti.views.util import search_content
        request = DummyRequest()
        doc1, doc11, doc12, file1 = create_contents(root)
        results = search_content(u'this is a file', request)
        assert len(results) == 1
        assert results[0]['name'] == 'file1'
        assert results[0]['title'] == 'First File'
        assert results[0]['path'] == '/doc1/file1/'

    def test_search_content_without_permission(self, config, root):
        from kotti.views.util import search_content
        request = DummyRequest()
        create_contents(root)
        config.testing_securitypolicy(permissive=False)
        results = search_content(u'Document', request)
        assert len(results) == 0

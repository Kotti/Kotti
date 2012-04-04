from kotti.testing import UnitTestBase


class TestTag(UnitTestBase):

    def test_empty(self):
        from kotti.resources import get_root
        assert get_root().tags == []

    def test_tags(self):
        from kotti.resources import Tag
        new_tag = Tag(u"test tag")
        assert str(new_tag) == "<Tag ('test tag')>"

    def test_add(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents

        root = get_root()
        root.tags = [u'tag 1', u'tag 2']
        result = DBSession.query(Tag).filter(TagsToContents.items == root).all()
        assert result[0].items == [root]
        assert root.tags == [u'tag 1', u'tag 2']
        assert len(DBSession.query(Tag).all()) == 2

    def test_edit(self):
        from kotti.resources import get_root

        root = get_root()
        root.tags = [u'tag 1', u'tag_2']
        assert root._tags[0].tag.title == u'tag 1'
        root.tags = [u'edited tag', u'tag_2']
        assert root._tags[0].tag.title == u'edited tag'

    def test_association_proxy(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = ['tag 1', 'tag 2', ]
        assert root[u'content_1'].tags == ['tag 1', 'tag 2', ]
        assert type(root[u'content_1']._tags[0]) == TagsToContents
        assert type(root[u'content_1']._tags[0].tag) == Tag
        assert root[u'content_1']._tags[0].tag.title == u'tag 1'
        assert root[u'content_1']._tags[0].position == 0
        assert root[u'content_1']._tags[1].tag.title == u'tag 2'
        assert root[u'content_1']._tags[1].position == 1
        assert len(root[u'content_1']._tags) == 2

        root[u'content_2'] = Content()
        root[u'content_2'].tags = [u'tag 1', u'tag 3']
        assert len(root[u'content_2']._tags) == 2
        assert root[u'content_2']._tags[0].tag.title == u'tag 1'
        assert root[u'content_2']._tags[0].position == 0
        assert root[u'content_2']._tags[1].tag.title == u'tag 3'
        assert root[u'content_2']._tags[1].position == 1
        assert len(DBSession.query(Tag).all()) == 3

    def test_widget(self):
        # TODO: test serialze
        import colander
        from kotti.views.widget import TagItWidget

        field = DummyField()
        widget = TagItWidget()
        result = widget.deserialize(field, colander.null)
        assert result == colander.null
        result = widget.deserialize(field, ['a', 'list'])
        assert result == ('a', 'list')
        result = widget.deserialize(field, 'a,b and c,d')
        assert result == ['a', 'b and c', 'd']


class DummyField(object):
    pass

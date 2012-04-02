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
        from kotti.resources import Tag

        root = get_root()
        root.tags = [u'adding tag 1', u'adding tag 2']
        result = DBSession.query(Tag).filter(Tag.items.contains(root)).all()
        assert root.tag_items == result
        assert result[0].items == [root]
        assert root.tags == [u'adding tag 1', u'adding tag 2']

    def test_edit(self):
        from kotti.resources import get_root

        root = get_root()
        root.tags = [u'tag 1', u'tag_2']
        assert root.tag_items[0].title == u'tag 1'
        root.tags = [u'edited tag', u'tag_2']
        assert root.tag_items[0].title == u'edited tag'

    def test_proxy(self):
        from kotti.resources import Content, Tag

        content = Content()
        content.tags = ['tag 1', 'tag 2', ]
        assert content.tags == ['tag 1', 'tag 2', ]
        assert type(content.tag_items[0]) == Tag
        assert content.tag_items[0].title == 'tag 1'
        assert content.tag_items[1].title == 'tag 2'

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

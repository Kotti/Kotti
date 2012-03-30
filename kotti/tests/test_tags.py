from kotti.testing import UnitTestBase


class TestTag(UnitTestBase):

    def test_empty(self):
        from kotti.resources import get_root
        get_root().tags == []

    def test_tags(self):
        from kotti.resources import Tag
        new_tag = Tag(u"test tag")
        assert str(new_tag) == "<Tag ('test tag')>"

    def test_add(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag

        root = get_root()
        new_tag = Tag(u'new tag')
        root.tags = [new_tag]
        result = DBSession.query(Tag).filter(Tag.items.contains(root)).all()
        assert result == [new_tag]
        assert new_tag.items == [root]
        assert root.tags == [new_tag]

    def test_edit(self):
        from kotti.resources import get_root
        from kotti.resources import Tag

        root = get_root()
        tag_1 = Tag(u'tag')
        tag_2 = Tag(u'another tag')
        root.tags = [tag_1, tag_2]
        tag_2.title = u'edited another tag'
        assert root.tags[1].title == u'edited another tag'

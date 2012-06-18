import colander
from mock import Mock

from kotti.testing import (
    UnitTestBase,
    EventTestBase,
    DummyRequest,
)


class DummyContext(object):
    view_name = u'view_name'
    tags = [u'tag 1', u'tag 2', u'tag 3', ]


class TestTags(EventTestBase, UnitTestBase):
    def test_empty(self):
        from kotti.resources import get_root
        assert get_root().tags == []

    def test_tags(self):
        from kotti.resources import Tag
        new_tag = Tag(title=u"test tag")
        assert str(new_tag) == "<Tag ('test tag')>"

    def test_add(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents

        root = get_root()
        root.tags = [u'tag 1', u'tag 2']
        result = DBSession.query(Tag).filter(TagsToContents.item == root).all()
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
        root[u'content_1'].tags = [u'tag 1', u'tag 2', ]
        assert root[u'content_1'].tags == [u'tag 1', u'tag 2', ]
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

    def test_delete_tag_doesnt_touch_content(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = [u'my tag']

        ses = DBSession
        assert ses.query(Content).filter_by(name=u'content_1').count() == 1
        ses.delete(ses.query(Tag).filter_by(title=u'my tag').one())
        assert ses.query(Content).filter_by(name=u'content_1').count() == 1

    def test_delete_content_deletes_orphaned_tags(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_2'] = Content()
        root[u'content_1'].tags = [u'tag 1', u'tag 2']
        root[u'content_2'].tags = [u'tag 2']
        assert DBSession.query(Tag).count() == 2
        del root[u'content_1']
        assert DBSession.query(Tag).one().title == u'tag 2'

    def test_delete_tag_assignment_doesnt_touch_content(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = [u'my tag']

        ses = DBSession
        assert ses.query(Tag).count() == 1
        assert ses.query(Content).filter_by(name=u'content_1').count() == 1
        ses.delete(ses.query(TagsToContents).one())
        assert ses.query(Content).filter_by(name=u'content_1').count() == 1

    def test_delete_tag_assignment_delete_tag(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = [u'my tag']

        ses = DBSession
        assert ses.query(Tag).count() == 1
        ses.delete(ses.query(TagsToContents).one())
        assert ses.query(Tag).count() == 0

    def test_copy_content_copy_tags(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content

        ses = DBSession
        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = [u'my tag']
        assert ses.query(Tag).count() == 1
        assert ses.query(TagsToContents).count() == 1

        root[u'content_2'] = root[u'content_1'].copy()
        DBSession.flush()
        assert root[u'content_1'].tags == [u'my tag']
        assert root[u'content_2'].tags == [u'my tag']
        assert ses.query(Tag).count() == 1
        assert ses.query(TagsToContents).count() == 2

    def test_cut_and_paste_content_copy_tags(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.edit import paste_node

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = [u'my tag']
        assert ses.query(Tag).count() == 1
        assert ses.query(TagsToContents).count() == 1

        request = DummyRequest()
        request.params['paste'] = u'on'
        request.session['kotti.paste'] = (root[u'content_1'].id, 'cut')
        paste_node(root[u'folder_1'], request)
        assert root[u'folder_1'][u'content_1'].tags == [u'my tag']
        assert ses.query(Tag).count() == 1
        assert ses.query(TagsToContents).count() == 1

    def test_copy_and_paste_content_copy_tags(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.edit import paste_node

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'content_1'] = Content()
        root[u'content_1'].tags = [u'my tag']
        assert ses.query(Tag).count() == 1
        assert ses.query(TagsToContents).count() == 1

        request = DummyRequest()
        request.params['paste'] = u'on'
        request.session['kotti.paste'] = (root[u'content_1'].id, 'copy')
        paste_node(root[u'folder_1'], request)
        assert root[u'content_1'].tags == [u'my tag']
        assert root[u'folder_1'][u'content_1'].tags == [u'my tag']
        assert ses.query(Tag).count() == 1
        assert ses.query(TagsToContents).count() == 2

    def test_delete_content_delete_tags_and_assignments(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.edit import delete_node

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'folder_1'].tags = [u'first tag']
        root[u'folder_1'][u'content_1'] = Content()
        root[u'folder_1'][u'content_1'].tags = [u'second tag']
        root[u'folder_1'][u'content_2'] = Content()
        root[u'folder_1'][u'content_2'].tags = [u'third tag']
        assert ses.query(Tag).count() == 3
        assert ses.query(TagsToContents).count() == 3

        request = DummyRequest()
        request.POST['delete'] = 'on'
        delete_node(root[u'folder_1'], request)
        assert ses.query(Tag).count() == 0
        assert ses.query(TagsToContents).count() == 0

    def test_get_content_items_from_tag(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, Content

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'folder_1'].tags = [u'first tag', u'second tag']
        root[u'folder_1'][u'content_1'] = Content()
        root[u'folder_1'][u'content_1'].tags = [u'third tag', ]
        root[u'folder_1'][u'content_2'] = Content()
        root[u'folder_1'][u'content_2'].tags = [u'first tag', u'third tag']
        first_tag = ses.query(Tag).filter(Tag.title == u'first tag').one()
        assert [rel.name for rel in first_tag.items] == [
            u'folder_1', u'content_2']
        second_tag = ses.query(Tag).filter(Tag.title == u'second tag').one()
        assert [rel.name for rel in second_tag.items] == [u'folder_1']
        third_tag = ses.query(Tag).filter(Tag.title == u'third tag').one()
        assert [rel.name for rel in third_tag.items] == [
            u'content_1', u'content_2']

    def test_get_content_items_for_tag_title(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import Tag, TagsToContents, Content

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'folder_1'].tags = [u'first tag', u'second tag']
        root[u'folder_1'][u'content_1'] = Content()
        root[u'folder_1'][u'content_1'].tags = [u'third tag', ]
        root[u'folder_1'][u'content_2'] = Content()
        root[u'folder_1'][u'content_2'].tags = [u'first tag', u'third tag']

        result = ses.query(Content).join(TagsToContents).join(Tag).filter(
            Tag.title == u'first tag').all()
        assert [res.name for res in result] == [u'folder_1', u'content_2']
        result = ses.query(Content).join(TagsToContents).join(Tag).filter(
            Tag.title == u'second tag').all()
        assert [res.name for res in result] == [u'folder_1']
        result = ses.query(Content).join(TagsToContents).join(Tag).filter(
            Tag.title == u'third tag').all()
        assert [res.name for res in result] == [u'content_1', u'content_2']


class TestCommaSeparatedListWidget(UnitTestBase):
    def make_one(self):
        from kotti.views.form import CommaSeparatedListWidget
        return CommaSeparatedListWidget(template='')

    def test_widget_serialize_none(self):
        field = Mock()
        widget = self.make_one()
        widget.serialize(field, None)
        field.renderer.assert_called_with(
            widget.template, field=field, cstruct=[])

    def test_widget_serialize_null(self):
        field = Mock()
        widget = self.make_one()
        widget.serialize(field, colander.null)
        field.renderer.assert_called_with(
            widget.template, field=field, cstruct=[])

    def test_widget_serialize(self):
        field = Mock()
        widget = self.make_one()
        widget.serialize(field, ['yes'])
        field.renderer.assert_called_with(
            widget.template, field=field, cstruct=['yes'])

    def test_widget_deserialize_null(self):
        assert (self.make_one().deserialize(None, colander.null) ==
                colander.null)

    def test_widget_deserialize(self):
        assert self.make_one().deserialize(None, 'foo,bar') == ['foo', 'bar']

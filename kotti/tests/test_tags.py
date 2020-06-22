import colander
from mock import Mock

from kotti.testing import DummyRequest


class DummyContext:
    view_name = "view_name"
    tags = ["tag 1", "tag 2", "tag 3"]


class TestTags:
    def test_empty(self, root):
        assert root.tags == []

    def test_tags(self, db_session):
        from kotti.resources import Tag

        new_tag = Tag(title="test tag")
        assert str(new_tag) == "<Tag ('test tag')>"

    def test_add(self, root):
        from kotti.resources import Tag, TagsToContents

        root.tags = ["tag 1", "tag 2"]
        result = Tag.query.filter(TagsToContents.item == root).all()
        assert result[0].items == [root]
        assert root.tags == ["tag 1", "tag 2"]
        assert len(Tag.query.all()) == 2

    def test_edit(self, root):
        root.tags = ["tag 1", "tag_2"]
        assert root._tags[0].tag.title == "tag 1"
        root.tags = ["edited tag", "tag_2"]
        assert root._tags[0].tag.title == "edited tag"

    def test_association_proxy(self, root):
        from kotti.resources import Tag, TagsToContents, Content

        root["content_1"] = Content()
        root["content_1"].tags = ["tag 1", "tag 2"]
        assert root["content_1"].tags == ["tag 1", "tag 2"]
        assert type(root["content_1"]._tags[0]) == TagsToContents
        assert type(root["content_1"]._tags[0].tag) == Tag
        assert root["content_1"]._tags[0].tag.title == "tag 1"
        assert root["content_1"]._tags[0].position == 0
        assert root["content_1"]._tags[1].tag.title == "tag 2"
        assert root["content_1"]._tags[1].position == 1
        assert len(root["content_1"]._tags) == 2

        root["content_2"] = Content()
        root["content_2"].tags = ["tag 1", "tag 3"]
        assert len(root["content_2"]._tags) == 2
        assert root["content_2"]._tags[0].tag.title == "tag 1"
        assert root["content_2"]._tags[0].position == 0
        assert root["content_2"]._tags[1].tag.title == "tag 3"
        assert root["content_2"]._tags[1].position == 1
        assert len(Tag.query.all()) == 3

    def test_delete_tag_doesnt_touch_content(self, root, db_session):
        from kotti.resources import Tag, Content

        root["content_1"] = Content()
        root["content_1"].tags = ["my tag"]

        assert Content.query.filter_by(name="content_1").count() == 1
        db_session.delete(Tag.query.filter_by(title="my tag").one())
        assert Content.query.filter_by(name="content_1").count() == 1

    def test_delete_content_deletes_orphaned_tags(self, root, events):
        from kotti.resources import Tag, Content

        root["content_1"] = Content()
        root["content_2"] = Content()
        root["content_1"].tags = ["tag 1", "tag 2"]
        root["content_2"].tags = ["tag 2"]
        assert Tag.query.count() == 2
        del root["content_1"]
        assert Tag.query.one().title == "tag 2"

    def test_delete_tag_assignment_doesnt_touch_content(self, root, db_session):
        from kotti.resources import Tag, TagsToContents, Content

        root["content_1"] = Content()
        root["content_1"].tags = ["my tag"]

        assert Tag.query.count() == 1
        assert Content.query.filter_by(name="content_1").count() == 1
        db_session.delete(TagsToContents.query.one())
        assert Content.query.filter_by(name="content_1").count() == 1

    def test_delete_tag_assignment_delete_tag(self, root, events, db_session):
        from kotti.resources import Tag, TagsToContents, Content

        root["content_1"] = Content()
        root["content_1"].tags = ["my tag"]

        assert Tag.query.count() == 1
        db_session.delete(TagsToContents.query.one())
        assert Tag.query.count() == 0

    def test_copy_content_copy_tags(self, root, db_session):
        from kotti.resources import Tag, TagsToContents, Content

        root["content_1"] = Content()
        root["content_1"].tags = ["my tag"]
        assert Tag.query.count() == 1
        assert TagsToContents.query.count() == 1

        root["content_2"] = root["content_1"].copy()
        db_session.flush()
        assert root["content_1"].tags == ["my tag"]
        assert root["content_2"].tags == ["my tag"]
        assert Tag.query.count() == 1
        assert TagsToContents.query.count() == 2

    def test_cut_and_paste_content_copy_tags(self, root):
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.edit.actions import NodeActions

        root["folder_1"] = Content()
        root["content_1"] = Content()
        root["content_1"].tags = ["my tag"]
        assert Tag.query.count() == 1
        assert TagsToContents.query.count() == 1

        request = DummyRequest()
        request.params["paste"] = "on"
        request.session["kotti.paste"] = ([root["content_1"].id], "cut")
        NodeActions(root["folder_1"], request).paste_nodes()
        assert root["folder_1"]["content_1"].tags == ["my tag"]
        assert Tag.query.count() == 1
        assert TagsToContents.query.count() == 1

    def test_copy_and_paste_content_copy_tags(self, root, events):
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.edit.actions import NodeActions

        root["folder_1"] = Content()
        root["content_1"] = Content()
        root["content_1"].tags = ["my tag"]
        assert Tag.query.count() == 1
        assert TagsToContents.query.count() == 1

        request = DummyRequest()
        request.params["paste"] = "on"
        request.session["kotti.paste"] = ([root["content_1"].id], "copy")
        NodeActions(root["folder_1"], request).paste_nodes()
        assert root["content_1"].tags == ["my tag"]
        assert root["folder_1"]["content_1"].tags == ["my tag"]
        assert Tag.query.count() == 1
        assert TagsToContents.query.count() == 2

    def test_delete_content_delete_tags_and_assignments(self, root, events):
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.edit.actions import NodeActions

        root["folder_1"] = Content()
        root["folder_1"].tags = ["first tag"]
        root["folder_1"]["content_1"] = Content()
        root["folder_1"]["content_1"].tags = ["second tag"]
        root["folder_1"]["content_2"] = Content()
        root["folder_1"]["content_2"].tags = ["third tag"]
        assert Tag.query.count() == 3
        assert TagsToContents.query.count() == 3

        request = DummyRequest()
        request.POST["delete"] = "delete"
        NodeActions(root["folder_1"], request).delete_node()
        assert Tag.query.count() == 0
        assert TagsToContents.query.count() == 0

    def test_get_content_items_from_tag(self, root):
        from kotti.resources import Tag, Content

        root["folder_1"] = Content()
        root["folder_1"].tags = ["first tag", "second tag"]
        root["folder_1"]["content_1"] = Content()
        root["folder_1"]["content_1"].tags = ["third tag"]
        root["folder_1"]["content_2"] = Content()
        root["folder_1"]["content_2"].tags = ["first tag", "third tag"]
        first_tag = Tag.query.filter(Tag.title == "first tag").one()
        assert [rel.name for rel in first_tag.items] == ["folder_1", "content_2"]
        second_tag = Tag.query.filter(Tag.title == "second tag").one()
        assert [rel.name for rel in second_tag.items] == ["folder_1"]
        third_tag = Tag.query.filter(Tag.title == "third tag").one()
        assert [rel.name for rel in third_tag.items] == ["content_1", "content_2"]

    def test_get_content_items_for_tag_title(self, root):
        from kotti.resources import Tag, TagsToContents, Content
        from kotti.views.util import content_with_tags

        root["folder_1"] = Content()
        root["folder_1"].tags = ["first tag", "second tag"]
        root["folder_1"]["content_1"] = Content()
        root["folder_1"]["content_1"].tags = ["third tag"]
        root["folder_1"]["content_2"] = Content()
        root["folder_1"]["content_2"].tags = ["first tag", "third tag"]

        result = (
            Content.query.join(TagsToContents)
            .join(Tag)
            .filter(Tag.title == "first tag")
            .all()
        )
        assert [res.name for res in result] == ["folder_1", "content_2"]
        result = (
            Content.query.join(TagsToContents)
            .join(Tag)
            .filter(Tag.title == "second tag")
            .all()
        )
        assert [res.name for res in result] == ["folder_1"]
        result = (
            Content.query.join(TagsToContents)
            .join(Tag)
            .filter(Tag.title == "third tag")
            .all()
        )
        assert sorted(res.name for res in result) == sorted(["content_1", "content_2"])

        # The same tests again, using content_with_tags():
        #
        #     About expected sort order:
        #
        #         In the first set of tests below, where we search by single
        #         tags, the query in the content_with_tags() function returns
        #         results in hierarchical order, from root.
        #
        # content_with_tags() is written to take a list of tags, but in the
        # default Kotti, presently, after some consideration about specialized
        # add-ons for searching, we do not support multiple tags searching, in
        # part to avoid establishing a specification.
        #
        result = content_with_tags(["first tag"])
        assert sorted([res.name for res in result]) == sorted(["folder_1", "content_2"])
        result = content_with_tags(["second tag"])
        assert sorted([res.name for res in result]) == sorted(["folder_1"])
        result = content_with_tags(["third tag"])
        assert sorted([res.name for res in result]) == sorted(
            ["content_1", "content_2"]
        )


class TestCommaSeparatedListWidget:
    def make_one(self):
        from kotti.views.form import CommaSeparatedListWidget

        return CommaSeparatedListWidget(template="")

    def test_widget_serialize_none(self):
        field = Mock()
        widget = self.make_one()
        widget.serialize(field, None)
        field.renderer.assert_called_with(widget.template, field=field, cstruct=[])

    def test_widget_serialize_null(self):
        field = Mock()
        widget = self.make_one()
        widget.serialize(field, colander.null)
        field.renderer.assert_called_with(widget.template, field=field, cstruct=[])

    def test_widget_serialize(self):
        field = Mock()
        widget = self.make_one()
        widget.serialize(field, ["yes"])
        field.renderer.assert_called_with(widget.template, field=field, cstruct=["yes"])

    def test_widget_deserialize_null(self):
        assert self.make_one().deserialize(None, colander.null) == colander.null

    def test_widget_deserialize(self):
        assert self.make_one().deserialize(None, "foo,bar") == ["foo", "bar"]

import warnings

from pytest import raises


def assert_deprecations(w, *msgs):

    assert len(w) == len(msgs)

    for i in range(len(w)):
        assert issubclass(w[i].category, DeprecationWarning)
        assert msgs[i] in str(w[i].message)


class TestToBeRemovedIn20:
    def test_type_info_action_links_deprecated(self, allwarnings):
        from kotti.resources import TypeInfo
        from kotti.util import LinkParent

        my_item = object()
        with warnings.catch_warnings(record=True) as wngs:
            # If there's a last LinkParent item, we'll assume that is
            # the action menu.
            TypeInfo(edit_links=[LinkParent("foo", [])], action_links=[my_item])
            assert wngs[0].category == DeprecationWarning

        with raises(ValueError):
            # If there's no last LinkParent item, we'll raise an
            # error, since we can't do anything useful with the link.
            TypeInfo(edit_links=[], action_links=[my_item])

    def test_object_after_delete(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.events import ObjectAfterDelete

            __ = ObjectAfterDelete  # pyflakes
            assert_deprecations(w, "Kotti 0.10")

    def test_translate_titles_deprecated(self, allwarnings):
        from kotti.views.edit import _translate_titles

        with warnings.catch_warnings(record=True) as w:
            info = [
                {"data": {"title": "_('Private')"}, "title": "_('Private')"},
                {"data": {"title": "_('Public')"}, "title": "_('Public')"},
            ]
            _translate_titles(info)
            assert_deprecations(w, "removed in Kotti 2.0.0")

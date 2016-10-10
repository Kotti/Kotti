# -*- coding: utf-8 -*-

import warnings

from pyramid.i18n import TranslationString
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
            TypeInfo(edit_links=[LinkParent('foo', [])],
                     action_links=[my_item])
            assert wngs[0].category == DeprecationWarning

        with raises(ValueError):
            # If there's no last LinkParent item, we'll raise an
            # error, since we can't do anything useful with the link.
            TypeInfo(edit_links=[], action_links=[my_item])

    def test_security_has_permission(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.security import has_permission
            __ = has_permission  # pyflakes
            assert_deprecations(w, "deprecated as of Kotti 1.0")

    def test_object_after_delete(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.events import ObjectAfterDelete
            __ = ObjectAfterDelete  # pyflakes
            assert_deprecations(w, "Kotti 0.10")

    def test_is_root_permission(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.views.util import is_root
            __ = is_root  # pyflakes
            assert_deprecations(w, "deprecated as of Kotti 1.0")

    def test_uploaded_file_response(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.views.file import UploadedFileResponse
            __ = UploadedFileResponse  # pyflakes
            assert_deprecations(w, "removed in Kotti 2.0.0")

    def test_image_deprecations(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.interfaces import IImage
            from kotti.resources import Image
            from kotti.views.edit.content import ImageAddForm
            from kotti.views.edit.content import ImageEditForm
            from kotti.views.image import _load_image_scales
            from kotti.views.image import image_scales
            from kotti.views.image import ImageView
            from kotti.views.image import includeme
            __ = (IImage, Image, _load_image_scales, image_scales, ImageView,
                  includeme, ImageAddForm, ImageEditForm)  # pyflakes
            assert_deprecations(w, *('kotti_image', ) * 8)

    def test_translate_titles_deprecated(self, allwarnings):
        from kotti.views.edit import _translate_titles

        with warnings.catch_warnings(record=True) as w:
            info = [
                {'data': {'title': u"_(u'Private')"}, 'title': u"_(u'Private')", },
                {'data': {'title': u"_(u'Public')"}, 'title': u"_(u'Public')", },
            ]
            _translate_titles(info)
            assert_deprecations(w, "removed in Kotti 2.0.0")

    def test_testing_root_factory(self, allwarnings):
        with warnings.catch_warnings(record=True) as w:
            from kotti.testing import TestingRootFactory
            __ = TestingRootFactory  # pyflakes
            assert_deprecations(w, "will be no longer available starting with "
                                   "Kotti 2.0.0.")

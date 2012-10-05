# -*- coding: utf-8 -*-

from kotti.resources import get_root
from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase
from kotti.views.edit.default_view_selection import DefaultViewSelection
from pyramid.httpexceptions import HTTPFound


class TestDefaultViewSelection(UnitTestBase):

    def test__is_valid_view(self):

        context = get_root()
        request = DummyRequest()

        view = DefaultViewSelection(context, request)

        #assert view._is_valid_view("folder_view") == True
        #assert view._is_valid_view("foo_view") == False

    def test_default_view_selection(self):

        context = get_root()
        request = DummyRequest()

        view = DefaultViewSelection(context, request)

        sviews = view.default_view_selector()

        assert 'selectable_default_views' in sviews

        # the root should have at least the default view and te folder_view
        assert len(sviews['selectable_default_views']) == 2

        # the first view is always the default view
        assert sviews['selectable_default_views'][0]['is_current'] is True
        assert sviews['selectable_default_views'][0]['name'] == 'default'
        assert sviews['selectable_default_views'][0]['title'] == 'Default view'

        assert sviews['selectable_default_views'][1]['is_current'] is False

        # set the default view to folder_view
        request = DummyRequest(GET={'view_name': 'folder_view'})
        view = DefaultViewSelection(context, request)

        assert type(view.set_default_view()) == HTTPFound
        #assert context.default_view == 'folder_view'

# -*- coding: utf-8 -*-
import warnings
from kotti.resources import get_root
from kotti.resources import IContent
from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase
from kotti.views.edit.default_view_selection import DefaultViewSelection
from pyramid.httpexceptions import HTTPFound


class TestDefaultViewSelection(UnitTestBase):

    def test__is_valid_view(self):

        self.config.add_view(
            context=IContent,
            name='contents',
            permission='view',
            renderer='kotti:templates/view/folder.pt',
        )

        context = get_root()
        request = DummyRequest()

        view = DefaultViewSelection(context, request)

        assert view._is_valid_view("contents") is True
        assert view._is_valid_view("foo") is False

    def test_default_view_selection(self):

        self.config.add_view(
            context=IContent,
            name='contents',
            permission='view',
            renderer='kotti:templates/view/folder.pt',
        )

        context = get_root()
        request = DummyRequest()

        view = DefaultViewSelection(context, request)

        sviews = view.default_view_selector()

        assert 'selectable_default_views' in sviews

        # the root should have at least the default view and the contents view
        assert len(sviews['selectable_default_views']) > 1

        # the first view is always the default view
        assert sviews['selectable_default_views'][0]['is_current'] is True
        assert sviews['selectable_default_views'][0]['name'] == 'default'
        assert sviews['selectable_default_views'][0]['title'] == 'Default view'

        assert sviews['selectable_default_views'][1]['is_current'] is False

        # set the default view to contents view
        request = DummyRequest(GET={'view_name': 'contents'})
        view = DefaultViewSelection(context, request)

        assert type(view.set_default_view()) == HTTPFound
        assert context.default_view == 'contents'

        # set back to default
        request = DummyRequest(GET={'view_name': 'default'})
        view = DefaultViewSelection(context, request)

        assert type(view.set_default_view()) == HTTPFound
        assert context.default_view is None

        # try to set non existing view
        request = DummyRequest(GET={'view_name': 'nonexisting'})
        view = DefaultViewSelection(context, request)

        assert type(view.set_default_view()) == HTTPFound
        assert context.default_view is None

    def test_warning_for_non_registered_views(self):

        with warnings.catch_warnings(record=True) as w:

            DefaultViewSelection(get_root(), DummyRequest()).default_view_selector()

            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)
            assert str(w[-1].message) == "No view called 'contents' is registered for <Document 1 at />"

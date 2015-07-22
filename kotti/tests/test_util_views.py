# coding:utf8
import time
import decimal
from mock import patch
from mock import Mock
from mock import MagicMock
from pyramid.request import Response
from pytest import raises

from kotti.testing import Dummy
from kotti.testing import DummyRequest


# filter deprecation warnings for code that is still tested...
from warnings import filterwarnings
filterwarnings('ignore', '^kotti.views.slots.register is deprecated')


def create_contents(root):
    from kotti.resources import Content

    # root -> a --> aa
    #         |
    #         \ --> ab
    #         |
    #         \ --> ac --> aca
    #               |
    #               \ --> acb

    a = root['a'] = Content()
    aa = root['a']['aa'] = Content()
    ab = root['a']['ab'] = Content()
    ac = root['a']['ac'] = Content()
    aca = ac['aca'] = Content()
    acb = ac['acb'] = Content()
    return a, aa, ab, ac, aca, acb


class TestTemplateAPI:
    def make(self, context=None, request=None, id=1, **kwargs):
        from kotti.resources import get_root
        from kotti.views.util import TemplateAPI

        if context is None:
            context = get_root()
        if request is None:
            request = DummyRequest()
        return TemplateAPI(context, request, **kwargs)

    def test_page_title(self, db_session):
        api = self.make()
        api.context.title = u"Hello, world!"
        assert api.page_title == u"Hello, world! - Hello, world!"

        api = self.make()
        api.context.title = u"Hello, world!"
        api.site_title = u"Wasnhierlos"
        assert api.page_title == u"Hello, world! - Wasnhierlos"

    def test_site_title(self, db_session):
        with patch('kotti.views.util.get_settings',
                   return_value={'kotti.site_title': u'This is it.'}):
            api = self.make()
            assert api.site_title == u'This is it.'

    def test_list_children(self, db_session):
        api = self.make()  # the default context is root
        root = api.context
        assert len(api.list_children(root)) == 0

        # Now try it on a little graph:
        a, aa, ab, ac, aca, acb = create_contents(root)
        with patch('kotti.views.util.has_permission', return_value=True):
            assert api.list_children() == [a]
            assert api.list_children(root) == [a]
            assert api.list_children(a) == [aa, ab, ac]
            assert api.list_children(aca) == []

        # Try permissions
        with patch('kotti.views.util.has_permission') as has_permission:
            has_permission.return_value = False
            assert api.list_children(root) == []
            has_permission.assert_called_once_with('view', a, api.request)

        with patch('kotti.views.util.has_permission') as has_permission:
            has_permission.return_value = False
            assert api.list_children(root, permission='edit') == []
            has_permission.assert_called_once_with('edit', a, api.request)

    def test_root(self, db_session):
        api = self.make()
        root = api.context
        a, aa, ab, ac, aca, acb = create_contents(root)
        assert self.make().root == root
        assert self.make(acb).root == root

    def test_navigation_root(self, db_session):
        from zope.interface import alsoProvides
        from kotti.interfaces import INavigationRoot

        api = self.make()
        root = api.context
        a, aa, ab, ac, aca, acb = create_contents(root)
        assert self.make().navigation_root == root
        assert self.make(acb).navigation_root == root

        alsoProvides(a, INavigationRoot)
        assert self.make(acb).navigation_root == a

    def test_breadcrumbs(self, db_session):
        api = self.make()
        root = api.context
        a, aa, ab, ac, aca, acb = create_contents(root)
        api.context = acb
        breadcrumbs = [b for b in api.breadcrumbs]
        assert breadcrumbs == [root, a, ac, acb]

    def test_breadcrumbs_with_navigation_root(self, db_session):
        from zope.interface import alsoProvides
        from kotti.interfaces import INavigationRoot

        api = self.make()
        root = api.context
        a, aa, ab, ac, aca, acb = create_contents(root)
        api.context = acb
        alsoProvides(a, INavigationRoot)
        breadcrumbs = [b for b in api.breadcrumbs]
        assert breadcrumbs == [a, ac, acb]

    def test_has_permission(self, db_session):
        with patch('kotti.views.util.has_permission') as has_permission:
            api = self.make()
            api.has_permission('drink')
            has_permission.assert_called_with('drink', api.root, api.request)

    def test_edit_links(self, config, db_session):
        from kotti import views
        from kotti.views.edit import actions, content, default_views
        from kotti.views import users
        from kotti.util import Link

        api = self.make()
        config.include(views)
        config.include(actions)
        config.include(content)
        config.include(default_views)
        config.include(users)

        assert (api.edit_links[:3] == [
            Link('contents', u'Contents'),
            Link('edit', u'Edit'),
            Link('share', u'Share'),
            ])

        # Edit links are controlled through
        # 'root.type_info.edit_links' and the permissions that guard
        # these:
        class MyLink(Link):
            permit = True

            def permitted(self, context, request):
                return self.permit

        open_link = MyLink('open')
        secure_link = MyLink('secure')
        secure_link.permit = False

        root = api.root
        root.type_info = root.type_info.copy(
            edit_links=[open_link, secure_link])
        api = self.make()
        assert api.edit_links == [open_link]

    def test_default_actions(self):
        from kotti.resources import default_actions, Document
        from kotti.util import Link

        default_actions.append(Link('test', u'Test'))
        assert Document().type_info.edit_links[-1].children[-1].name == 'test'

    def test_find_edit_view_not_permitted(self, db_session):
        with patch('kotti.views.util.view_permitted', return_value=False):
            api = self.make()
            api.request.view_name = u'edit'
            assert api.find_edit_view(api.context) == u''

    def test_find_edit_view(self, db_session):
        with patch('kotti.views.util.view_permitted', return_value=True):
            api = self.make()
            api.request.view_name = u'share'
            assert api.find_edit_view(api.context) == u'share'

    def test_macro(self, db_session):
        with patch('kotti.views.util.get_renderer') as get_renderer:
            get_renderer().implementation().macros = MagicMock()
            api = self.make()
            macro = api.macro('mypackage:mytemplate.pt')
            get_renderer.assert_called_with('mypackage:mytemplate.pt')
            assert get_renderer().implementation().macros['main'] == macro

    def test_macro_bare_with_master(self, db_session):
        # getting EDIT_MASTER when bare=True will return BARE_MASTER
        with patch('kotti.views.util.get_renderer') as get_renderer:
            get_renderer().implementation().macros = MagicMock()
            api = self.make(bare=True)
            macro = api.macro(api.EDIT_MASTER)
            get_renderer.assert_called_with(api.BARE_MASTER)
            assert get_renderer().implementation().macros['main'] == macro

    def test_macro_bare_without_master(self, db_session):
        # getting other templates when bare=True
        with patch('kotti.views.util.get_renderer') as get_renderer:
            get_renderer().implementation().macros = MagicMock()
            api = self.make(bare=True)
            macro = api.macro('mypackage:mytemplate.pt')
            get_renderer.assert_called_with('mypackage:mytemplate.pt')
            assert get_renderer().implementation().macros['main'] == macro

    def test_url_without_context(self, db_session):
        context, request = object(), MagicMock()
        api = self.make(context=context, request=request)
        api.url()
        request.resource_url.assert_called_with(context)

    def test_url_with_context(self, db_session):
        context, request = object(), MagicMock()
        api = self.make(request=request)
        api.url(context)
        request.resource_url.assert_called_with(context)

    def test_url_with_context_and_elements(self, db_session):
        context, request = object(), MagicMock()
        api = self.make(request=request)
        api.url(context, 'first', second='second')
        request.resource_url.assert_called_with(
            context, 'first', second='second')

    def test_bare(self, db_session):
        # By default, no "bare" templates are used:
        api = self.make()
        assert api.bare is None

        # We can ask for "bare" templates explicitely:
        api = self.make(bare=True)
        assert api.bare is True

        # An XHR request will always result in bare master templates:
        request = DummyRequest()
        request.is_xhr = True
        api = self.make(request=request)
        assert api.bare is True

        # unless overridden:
        api = self.make(request=request, bare=False)
        assert api.bare is False

    def test_assign_to_slots(self, config, db_session, events):
        from kotti.views.slots import assign_slot

        def foo(context, request):
            greeting = request.POST['greeting']
            return Response(u"{0} world!".format(greeting))
        config.add_view(foo, name='foo')
        assign_slot('foo', 'left', params=dict(greeting=u"Y\u0153"))

        api = self.make()
        assert api.slots.left == [u"Y\u0153 world!"]

    def test_assign_to_slot_predicate_mismatch(self, config, db_session,
                                               events):
        from kotti.views.slots import assign_slot

        def special(context, request):
            return Response(u"Hello world!")
        assign_slot('special', 'right')

        config.add_view(special, name='special', request_method="GET")
        api = self.make()
        assert api.slots.right == []

        config.add_view(special, name='special')
        api = self.make()
        assert api.slots.right == [u"Hello world!"]

    def test_assign_to_slot_forbidden(self, config, db_session,
                                      events):
        from kotti.views.slots import assign_slot
        from pyramid.exceptions import HTTPForbidden

        def special(context, request):
            return Response(u"Hello world!")
        assign_slot('special', 'right')

        config.add_view(special, name='special', permission='admin')
        # the slot rendering must not fail if a HTTPForbidden exception
        api = self.make()
        with patch('kotti.views.slots.render_view') as render_view:
            render_view.side_effect = HTTPForbidden()
            assert api.slots.right == []

    def test_assign_slot_bad_name(self):
        from kotti.views.slots import assign_slot

        with raises(KeyError):
            assign_slot('viewname', 'noslotlikethis')

    def test_slot_request_has_attributes(self, config, db_session, events):
        from kotti.views.slots import assign_slot

        def my_viewlet(request):
            assert hasattr(request, 'registry')
            assert hasattr(request, 'context')
            assert hasattr(request, 'user')
            return Response(u"Hello world!")
        assign_slot('my-viewlet', 'right')

        config.add_view(my_viewlet, name='my-viewlet')
        api = self.make()
        assert api.slots.right == [u"Hello world!"]

    def test_slot_request_has_parameters(self, config, db_session):
        from kotti.views.slots import assign_slot

        def foo(context, request):
            bar = request.POST['bar']
            return Response(u"{0} world!".format(bar))
        config.add_view(foo, name='foo')
        assign_slot('foo', 'left', params=dict(greeting=u"Y\u0153"))

        request = DummyRequest()
        request.params['bar'] = u'Hello'
        api = self.make(request=request)
        assert api.slots.left == [u"Hello world!"]

    def test_slot_view_know_slot(self, config, db_session):
        from kotti.views.slots import assign_slot

        def foo(context, request):
            slot = request.kotti_slot
            return Response(u"I'm in slot {0}.".format(slot))
        config.add_view(foo, name='foo')
        assign_slot('foo', 'beforebodyend')
        assign_slot('foo', 'right')

        request = DummyRequest()
        api = self.make(request=request)
        assert api.slots.beforebodyend == [u"I'm in slot beforebodyend."]
        assert api.slots.right == [u"I'm in slot right."]

    # def test_deprecated_slots(self, db_session):
    #     from kotti.views.slots import register, RenderAboveContent

    #     def render_something(context, request):
    #         return u"Hello, %s!" % context.title
    #     register(RenderAboveContent, None, render_something)

    #     api = self.make()
    #     assert (api.slots.abovecontent == [u'Hello, %s!' % api.context.title])

    #     # Slot renderers may also return lists:
    #     def render_a_list(context, request):
    #         return [u"a", u"list"]
    #     register(RenderAboveContent, None, render_a_list)
    #     api = self.make()
    #     assert (
    #         api.slots.abovecontent ==
    #         [u'Hello, %s!' % api.context.title, u'a', u'list']
    #         )

    #     with raises(AttributeError):
    #         api.slots.foobar

    def test_slots_only_rendered_when_accessed(self, config, events):
        from kotti.views.slots import assign_slot

        called = []

        def foo(context, request):
            called.append(True)
            return Response(u"")

        config.add_view(foo, name='foo')
        assign_slot('foo', 'abovecontent')

        api = self.make()
        api.slots.belowcontent
        assert called == []

        api.slots.abovecontent
        assert len(called) == 1
        api.slots.abovecontent
        assert len(called) == 1

    def test_format_currency(self, db_session):
        api = self.make()
        assert u'€13.99' == api.format_currency(13.99, 'EUR')
        assert u'$15,499.12' == api.format_currency(15499.12, 'USD')
        assert u'€1' == api.format_currency(1, format=u'€#,##0',
                                            currency='EUR')
        assert u'CHF3.14' == api.format_currency(
            decimal.Decimal((0, (3, 1, 4), -2)), 'CHF')

    def test_format_datetime(self, db_session):
        import datetime
        from babel.dates import format_datetime
        from babel.core import UnknownLocaleError
        api = self.make()
        first = datetime.datetime(2012, 1, 1, 0)
        assert (
            api.format_datetime(first) ==
            format_datetime(first, format='medium', locale='en'))
        assert (
            api.format_datetime(time.mktime(first.timetuple())) ==
            format_datetime(first, format='medium', locale='en'))
        assert (
            api.format_datetime(first, format='short') ==
            format_datetime(first, format='short', locale='en'))
        api.locale_name = 'unknown'
        with raises(UnknownLocaleError):
            api.format_datetime(first)

    def test_format_date(self, db_session):
        import datetime
        from babel.dates import format_date
        from babel.core import UnknownLocaleError
        api = self.make()
        first = datetime.date(2012, 1, 1)
        assert (
            api.format_date(first) ==
            format_date(first, format='medium', locale='en'))
        assert (
            api.format_date(first, format='short') ==
            format_date(first, format='short', locale='en'))
        api.locale_name = 'unknown'
        with raises(UnknownLocaleError):
            api.format_date(first)

    def test_format_time(self, db_session):
        import datetime
        from babel.dates import format_time
        from babel.core import UnknownLocaleError
        api = self.make()
        first = datetime.time(23, 59)
        assert (
            api.format_time(first) ==
            format_time(first, format='medium', locale='en'))
        assert (
            api.format_time(first, format='short') ==
            format_time(first, format='short', locale='en'))
        api.locale_name = 'unknown'
        with raises(UnknownLocaleError):
            api.format_time(first)

    def test_render_view(self, config, db_session):
        def first_view(context, request):
            return Response(u'first')

        def second_view(context, request):
            return Response(u'second')

        config.add_view(first_view, name='')
        config.add_view(second_view, name='second')
        api = self.make()
        assert api.render_view().__unicode__() == u'first'
        assert api.render_view('second').__unicode__() == u'second'
        assert api.render_view(
            context=api.context, request=api.request).__unicode__() == u'first'

    def test_render_template(self, config, db_session):
        renderer = MagicMock()
        config.testing_add_renderer('my-rendererer', renderer)
        api = self.make()
        api.render_template('my-rendererer', some='variable')
        assert renderer.call_args[0][0] == {'some': 'variable'}

    def test_get_type(self, db_session):
        from kotti.resources import Document
        api = self.make()
        assert api.get_type('Document') == Document
        assert api.get_type('NoExist') is None

    def test_avatar_url(self, db_session):
        api = self.make()
        user = Dummy(email='daniel.nouri@gmail.com')
        result = api.avatar_url(user)
        assert result.startswith('https://secure.gravatar.com/avatar/'
                                 'd3aeefdd7afe103ab70875172135cab7')

    def test_avatar_url_request_user(self, db_session):
        api = self.make()
        api.request.user = Dummy(email='daniel.nouri@gmail.com')
        result = api.avatar_url()
        assert result.startswith('https://secure.gravatar.com/avatar/'
                                 'd3aeefdd7afe103ab70875172135cab7')


class TestViewUtil:
    def test_add_renderer_globals_json(self):
        from kotti.views.util import add_renderer_globals

        event = {'renderer_name': 'json'}
        add_renderer_globals(event)
        assert event.keys() == ['renderer_name']

    def test_add_renderer_globals_request_has_template_api(self):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        request.template_api = template_api = object()
        event = {'request': request, 'renderer_name': 'foo'}
        add_renderer_globals(event)
        assert event['api'] is template_api

    def test_add_renderer_globals(self, db_session):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        event = {
            'request': request,
            'context': object(),
            'renderer_name': 'foo', }
        add_renderer_globals(event)
        assert 'api' in event

    def test_add_renderer_globals_event_has_no_renderer_name(self, db_session):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        event = {
            'request': request,
            'context': object(),
            }
        add_renderer_globals(event)
        assert 'api' in event


class TestLocalNavigationSlot:
    def test_it(self, config, root):
        config.testing_add_renderer('kotti:templates/view/nav-local.pt')
        from zope.interface import alsoProvides
        from kotti.interfaces import INavigationRoot
        from kotti.views.navigation import local_navigation
        a, aa, ab, ac, aca, acb = create_contents(root)

        ret = local_navigation(ac, DummyRequest())
        assert ret == dict(parent=ac, children=[aca, acb])

        ret = local_navigation(acb, DummyRequest())
        assert ret == dict(parent=ac, children=[aca, acb])

        assert local_navigation(a.__parent__, DummyRequest())['parent'] is None

        alsoProvides(ac, INavigationRoot)
        assert local_navigation(ac, DummyRequest())['parent'] is None

    def test_no_permission(self, config, root):
        config.testing_add_renderer('kotti:templates/view/nav-local.pt')
        from kotti.views.navigation import local_navigation
        a, aa, ab, ac, aca, acb = create_contents(root)

        with patch('kotti.views.navigation.has_permission', return_value=True):
            assert local_navigation(ac, DummyRequest())['parent'] is not None

        with patch('kotti.views.navigation.has_permission', return_value=False):
            assert local_navigation(ac, DummyRequest())['parent'] is None

    def test_in_navigation(self, config, root):
        config.testing_add_renderer('kotti:templates/view/nav-local.pt')
        from kotti.views.navigation import local_navigation
        a, aa, ab, ac, aca, acb = create_contents(root)

        assert local_navigation(a, DummyRequest())['parent'] is not None
        aa.in_navigation = False
        ab.in_navigation = False
        ac.in_navigation = False
        assert local_navigation(a, DummyRequest())['parent'] is None


class TestNodesTree:
    def test_it(self, root):
        from kotti.views.util import nodes_tree

        a, aa, ab, ac, aca, acb = create_contents(root)
        aa.in_navigation = False  # nodes_tree doesn't care
        tree = nodes_tree(DummyRequest())
        assert tree.id == a.__parent__.id
        assert [ch.name for ch in tree.children] == [a.name]
        assert [ch.id for ch in tree.children[0].children] == [
            aa.id, ab.id, ac.id]

    def test_ordering(self, root):
        from kotti.views.util import nodes_tree

        a, aa, ab, ac, aca, acb = create_contents(root)
        a.children.insert(1, a.children.pop(0))
        tree = nodes_tree(DummyRequest())
        assert [ch.position for ch in tree.children[0].children] == [
            0, 1, 2]
        assert [ch.id for ch in tree.children[0].children] == [
            ab.id, aa.id, ac.id]

    def test_tolist(self, root):
        from kotti.views.util import nodes_tree

        a, aa, ab, ac, aca, acb = create_contents(root)
        tree = nodes_tree(DummyRequest(), context=a)
        assert [ch for ch in tree.tolist()] == [a, aa, ab, ac, aca, acb]

        tree = nodes_tree(DummyRequest(), context=ac)
        assert [ch for ch in tree.tolist()] == [ac, aca, acb]


class TestSettingHasValuePredicate:
    def test_basic(self):
        from kotti.views.util import SettingHasValuePredicate

        predicate = SettingHasValuePredicate(('mysetting', True), None)
        request = Mock()
        request.registry.settings = {'mysetting': 'True'}
        assert predicate(None, request) is True

        request.registry.settings = {'mysetting': '0'}
        assert predicate(None, request) is False

    def test_bool_value_assertion(self):
        from kotti.views.util import SettingHasValuePredicate

        with raises(ValueError):
            SettingHasValuePredicate(('mysetting', 'hello'), None)


class TestRootOnlyPredicate:
    def test_basic(self):
        from kotti.views.util import RootOnlyPredicate

        predicate = RootOnlyPredicate(True, None)
        request = Mock()
        root = request.root
        assert predicate(root, request) is True
        assert predicate(object(), request) is False

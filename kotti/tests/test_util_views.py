import time
from unittest import TestCase

from mock import patch
from mock import MagicMock

from kotti.testing import Dummy
from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

def create_contents(root=None):
    from kotti.resources import get_root
    from kotti.resources import Content

    # root -> a --> aa
    #         |
    #         \ --> ab
    #         |
    #         \ --> ac --> aca
    #               |
    #               \ --> acb
    if root is None:
        root = get_root()
    a = root['a'] = Content()
    aa = root['a']['aa'] = Content()
    ab = root['a']['ab'] = Content()
    ac = root['a']['ac'] = Content()
    aca = ac['aca'] = Content()
    acb = ac['acb'] = Content()
    return a, aa, ab, ac, aca, acb

class TestTemplateAPI(UnitTestBase):
    def make(self, context=None, request=None, id=1, **kwargs):
        from kotti import DBSession
        from kotti.resources import Node
        from kotti.views.util import TemplateAPI

        if context is None:
            session = DBSession()
            context = session.query(Node).get(id)
        if request is None:
            request = DummyRequest()
        return TemplateAPI(context, request, **kwargs)

    def test_page_title(self):
        api = self.make()
        api.context.title = u"Hello, world!"
        self.assertEqual(api.page_title, u"Hello, world! - Hello, world!")

        api = self.make()
        api.context.title = u"Hello, world!"
        api.site_title = u"Wasnhierlos"
        self.assertEqual(api.page_title, u"Hello, world! - Wasnhierlos")

    @patch('kotti.views.util.get_settings')
    def test_site_title(self, get_settings):
        get_settings.return_value = {'kotti.site_title': u'This is it.'}
        api = self.make()
        self.assertEqual(api.site_title, u'This is it.')

    @patch('kotti.views.util.has_permission')
    def test_list_children(self, has_permission):
        has_permission.return_value = True
        
        api = self.make() # the default context is root
        root = api.context
        self.assertEquals(len(api.list_children(root)), 0)

        # Now try it on a little graph:
        a, aa, ab, ac, aca, acb = create_contents(root)
        self.assertEquals(api.list_children(root), [a])
        self.assertEquals(api.list_children(a), [aa, ab, ac])
        self.assertEquals(api.list_children(aca), [])

        # Try permissions
        has_permission.reset_mock()
        has_permission.return_value = False
        self.assertEquals(api.list_children(root), [])
        has_permission.assert_called_once_with('view', a, api.request)

        has_permission.reset_mock()
        has_permission.return_value = False
        self.assertEquals(api.list_children(root, permission='edit'), [])
        has_permission.assert_called_once_with('edit', a, api.request)

    def test_root(self):
        api = self.make()
        root = api.context
        a, aa, ab, ac, aca, acb = create_contents(root)
        self.assertEquals(self.make().root, root)
        self.assertEquals(self.make(acb).root, root)

    @patch('kotti.views.util.has_permission')
    def test_has_permission(self, has_permission):
        api = self.make()
        api.has_permission('drink')
        has_permission.assert_called_with('drink', api.root, api.request)

    def test_edit_links(self):
        from kotti.util import ViewLink

        api = self.make()
        self.assertEqual(api.edit_links, [
            ViewLink('edit'),
            ViewLink('add'),
            ViewLink('move'),
            ViewLink('share'),
            ])

        # Edit links are controlled through
        # 'root.type_info.edit_links' and the permissions that guard
        # these:
        class MyLink(ViewLink):
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
        self.assertEqual(api.edit_links, [open_link])

    @patch('kotti.views.util.view_permitted')
    def test_find_edit_view_not_permitted(self, view_permitted):
        view_permitted.return_value = False
        api = self.make()
        api.request.view_name = u'edit'
        assert api.find_edit_view(api.context) == u''

    @patch('kotti.views.util.view_permitted')
    def test_find_edit_view(self, view_permitted):
        view_permitted.return_value = True
        api = self.make()
        api.request.view_name = u'share'
        assert api.find_edit_view(api.context) == u'share'

    @patch('kotti.views.util.get_renderer')
    def test_macro(self, get_renderer):
        api = self.make()
        macro = api.macro('mypackage:mytemplate.pt')
        get_renderer.assert_called_with('mypackage:mytemplate.pt')
        assert get_renderer().implementation().macros['main'] == macro

    @patch('kotti.views.util.get_renderer')
    def test_macro_bare_with_master(self, get_renderer):
        # getting EDIT_MASTER when bare=True will return BARE_MASTER
        api = self.make(bare=True)
        macro = api.macro(api.EDIT_MASTER)
        get_renderer.assert_called_with(api.BARE_MASTER)
        assert get_renderer().implementation().macros['main'] == macro

    @patch('kotti.views.util.get_renderer')
    def test_macro_bare_without_master(self, get_renderer):
        # getting other templates when bare=True
        api = self.make(bare=True)
        macro = api.macro('mypackage:mytemplate.pt')
        get_renderer.assert_called_with('mypackage:mytemplate.pt')
        assert get_renderer().implementation().macros['main'] == macro

    def test_url_without_context(self):
        context, request = object(), MagicMock()
        api = self.make(context=context, request=request)
        api.url()
        request.resource_url.assert_called_with(context)

    def test_url_with_context(self):
        context, request = object(), MagicMock()
        api = self.make(request=request)
        api.url(context)
        request.resource_url.assert_called_with(context)

    def test_url_with_context_and_elements(self):
        context, request = object(), MagicMock()
        api = self.make(request=request)
        api.url(context, 'first', second='second')
        request.resource_url.assert_called_with(
            context, 'first', second='second')

    def test_bare(self):
        # By default, no "bare" templates are used:
        api = self.make()
        self.assertEqual(api.bare, None)

        # We can ask for "bare" templates explicitely:
        api = self.make(bare=True)
        self.assertEqual(api.bare, True)

        # An XHR request will always result in bare master templates:
        request = DummyRequest()
        request.is_xhr = True
        api = self.make(request=request)
        self.assertEqual(api.bare, True)

        # unless overridden:
        api = self.make(request=request, bare=False)
        self.assertEqual(api.bare, False)

    def test_slots(self):
        from kotti.views.slots import register, RenderAboveContent
        def render_something(context, request):
            return u"Hello, %s!" % context.title
        register(RenderAboveContent, None, render_something)

        api = self.make()
        self.assertEqual(api.slots.abovecontent,
                         [u'Hello, %s!' % api.context.title])

        # Slot renderers may also return lists:
        def render_a_list(context, request):
            return [u"a", u"list"]
        register(RenderAboveContent, None, render_a_list)
        api = self.make()
        self.assertEqual(
            api.slots.abovecontent,
            [u'Hello, %s!' % api.context.title, u'a', u'list']
            )

        self.assertRaises(
            AttributeError,
            getattr, api.slots, 'foobar'
            )

    def test_slots_only_rendered_when_accessed(self):
        from kotti.views.slots import register, RenderAboveContent

        called = []
        def render_something(context, request):
            called.append(True)
        register(RenderAboveContent, None, render_something)
        
        api = self.make()
        api.slots.belowcontent
        self.assertFalse(called)

        api.slots.abovecontent
        self.assertEquals(len(called), 1)
        api.slots.abovecontent
        self.assertEquals(len(called), 1)

    def test_format_datetime(self):
        import datetime
        from babel.dates import format_datetime
        from babel.core import UnknownLocaleError
        api = self.make()
        first = datetime.datetime(2012, 1, 1, 0)
        self.assertEqual(
            api.format_datetime(first),
            format_datetime(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_datetime(time.mktime(first.timetuple())),
            format_datetime(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_datetime(first, format='short'),
            format_datetime(first, format='short', locale='en'),
            )
        api.locale_name = 'unknown'
        self.assertRaises(UnknownLocaleError, api.format_datetime, first)

    def test_format_date(self):
        import datetime
        from babel.dates import format_date
        from babel.core import UnknownLocaleError
        api = self.make()
        first = datetime.date(2012, 1, 1)
        self.assertEqual(
            api.format_date(first),
            format_date(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_date(first, format='short'),
            format_date(first, format='short', locale='en'),
            )
        api.locale_name = 'unknown'
        self.assertRaises(UnknownLocaleError, api.format_date, first)

    def test_format_time(self):
        import datetime
        from babel.dates import format_time
        from babel.core import UnknownLocaleError
        api = self.make()
        first = datetime.time(23, 59)
        self.assertEqual(
            api.format_time(first),
            format_time(first, format='medium', locale='en'),
            )
        self.assertEqual(
            api.format_time(first, format='short'),
            format_time(first, format='short', locale='en'),
            )
        api.locale_name = 'unknown'
        self.assertRaises(UnknownLocaleError, api.format_time, first)

    def test_render_view(self):
        from pyramid.response import Response
        def first_view(context, request):
            return Response(u'first')
        def second_view(context, request):
            return Response(u'second')
        self.config.add_view(first_view, name='')
        self.config.add_view(second_view, name='second')
        api = self.make()
        self.assertEqual(api.render_view().__unicode__(), u'first')
        self.assertEqual(api.render_view('second').__unicode__(), u'second')
        self.assertEqual(api.render_view(
            context=api.context, request=api.request).__unicode__(), u'first')

    def test_render_template(self):
        renderer = MagicMock()
        self.config.testing_add_renderer('my-rendererer', renderer)
        api = self.make()
        api.render_template('my-rendererer', some='variable')
        self.assertEqual(renderer.call_args[0][0], {'some': 'variable'})

    def test_get_type(self):
        from kotti.resources import Document
        api = self.make()
        self.assertEqual(api.get_type('Document'), Document)
        self.assertEqual(api.get_type('NoExist'), None)

class TestViewUtil(UnitTestBase):
    def test_add_renderer_globals_json(self):
        from kotti.views.util import add_renderer_globals

        event = {'renderer_name': 'json'}
        add_renderer_globals(event)
        self.assertEqual(event.keys(), ['renderer_name'])

    def test_add_renderer_globals_request_has_template_api(self):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        request.template_api = template_api = object()
        event = {'request': request, 'renderer_name': 'foo'}
        add_renderer_globals(event)
        self.assertTrue(event['api'] is template_api)

    def test_add_renderer_globals(self):
        from kotti.views.util import add_renderer_globals

        request = DummyRequest()
        event = {
            'request': request,
            'context': object(),
            'renderer_name': 'foo',
            }
        add_renderer_globals(event)
        self.assertTrue('api' in event)

class TestUtil(UnitTestBase):
    def test_title_to_name(self):
        from kotti.views.util import title_to_name
        self.assertEqual(title_to_name(u'Foo Bar'), u'foo-bar')

    def test_disambiguate_name(self):
        from kotti.views.util import disambiguate_name
        self.assertEqual(disambiguate_name(u'foo'), u'foo-1')
        self.assertEqual(disambiguate_name(u'foo-3'), u'foo-4')

    def test_ensure_view_selector(self):
        from kotti.views.util import ensure_view_selector
        wrapper = ensure_view_selector(None)
        request = DummyRequest(path='/edit')
        # Ignoring the result since it's not useful with DummyRequest.
        # We check that path_info was set accordingly though:
        wrapper(None, request)
        self.assertEqual(request.path_info, u'/@@edit')

class TestLocalNavigationSlot(UnitTestBase):
    def setUp(self):
        super(TestLocalNavigationSlot, self).setUp()
        self.renderer = self.config.testing_add_renderer(
            'kotti:templates/view/nav-local.pt')

    def test_it(self):
        from kotti.views.slots import render_local_navigation
        a, aa, ab, ac, aca, acb = create_contents()

        assert render_local_navigation(ac, DummyRequest()) is not None
        self.renderer.assert_(parent=ac, children=[aca, acb])

        assert render_local_navigation(acb, DummyRequest()) is not None
        self.renderer.assert_(parent=ac, children=[aca, acb])

        assert render_local_navigation(a.__parent__, DummyRequest()) is None

    @patch('kotti.views.slots.has_permission')
    def test_no_permission(self, has_permission):
        from kotti.views.slots import render_local_navigation
        a, aa, ab, ac, aca, acb = create_contents()

        has_permission.return_value = True
        assert render_local_navigation(ac, DummyRequest()) is not None

        has_permission.return_value = False
        assert render_local_navigation(ac, DummyRequest()) is None

    def test_in_navigation(self):
        from kotti.views.slots import render_local_navigation
        a, aa, ab, ac, aca, acb = create_contents()
        
        assert render_local_navigation(a, DummyRequest()) is not None
        aa.in_navigation = False
        ab.in_navigation = False
        ac.in_navigation = False
        assert render_local_navigation(a, DummyRequest()) is None

class TestNodesTree(UnitTestBase):
    def test_it(self):
        from kotti.views.util import nodes_tree

        a, aa, ab, ac, aca, acb = create_contents()
        aa.in_navigation = False # nodes_tree doesn't care
        tree = nodes_tree(DummyRequest())
        assert tree.id == a.__parent__.id
        assert [ch.name for ch in tree.children] == [a.name]
        assert [ch.id for ch in tree.children[0].children] == [
            aa.id, ab.id, ac.id]

    def test_ordering(self):
        from kotti.views.util import nodes_tree

        a, aa, ab, ac, aca, acb = create_contents()
        a.children.insert(1, a.children.pop(0))
        tree = nodes_tree(DummyRequest())
        assert [ch.position for ch in tree.children[0].children] == [
            0, 1, 2]
        assert [ch.id for ch in tree.children[0].children] == [
            ab.id, aa.id, ac.id]

class TestTemplateStructure(UnitTestBase):
    def test_getattr(self):
        from kotti.views.util import TemplateStructure

        item = TemplateStructure(u'123')
        assert item.split('2') == [u'1', u'3']

class TestBaseFormView(TestCase):
    def make(self):
        from kotti.views.util import BaseFormView
        return BaseFormView(Dummy(), DummyRequest())

    def test_init(self):
        from kotti.views.util import BaseFormView
        view = BaseFormView(Dummy(), DummyRequest(), more='args')
        assert view.more == 'args'

    def test_schema_factory_bind(self):
        view = self.make()
        schema = MagicMock()
        view.schema_factory = lambda: schema
        view.__call__()
        assert view.schema == schema.bind.return_value
        schema.bind.assert_called_with(request=view.request)

    def test_use_csrf_token(self):
        view = self.make()
        schema = view.schema = MagicMock()
        view.__call__()
        assert schema.children.append.called
        assert schema.children.append.call_args[0][0].name == 'csrf_token'

    def test_use_csrf_token_not(self):
        view = self.make()
        view.use_csrf_token = False
        schema = view.schema = MagicMock()
        view.__call__()
        assert not schema.children.append.called

class TestEditFormView(TestCase):
    def make(self):
        from kotti.views.util import EditFormView
        return EditFormView(Dummy(), DummyRequest())

    def test_before(self):
        view = self.make()
        view.context.three = 3
        form = Dummy()
        view.before(form)
        assert form.appstruct == {'three': 3}

    def test_save_success_calls_edit(self):
        view = self.make()
        view.edit = MagicMock()
        view.save_success({'three': 3})
        view.edit.assert_called_with(three=3)

    def test_save_success_redirects(self):
        view = self.make()
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == view.request.url

    def test_save_success_redirects_custom_url(self):
        view = self.make()
        view.success_url = 'there'
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == 'there'

class TestAddFormView(TestCase):
    def make(self):
        from kotti.views.util import AddFormView
        return AddFormView(Dummy(), DummyRequest())

    @patch('kotti.views.util.resource_url')
    def test_save_success_calls_add(self, resource_url):
        view = self.make()
        view.add = MagicMock()
        view.find_name = lambda appstruct: 'somename'
        view.save_success({'three': 3})
        view.add.assert_called_with(three=3)
        assert view.add.return_value == view.context['somename']

    @patch('kotti.views.util.resource_url')
    def test_save_success_redirects(self, resource_url):
        resource_url.return_value = 'someurl'
        view = self.make()
        view.add = MagicMock()
        view.find_name = lambda appstruct: 'somename'
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == 'someurl'

    def test_save_success_redirects_custom_url(self):
        view = self.make()
        view.add = MagicMock()
        view.success_url = 'there'
        view.find_name = lambda appstruct: 'somename'
        result = view.save_success({'three': 3})
        assert result.status == '302 Found'
        assert result.location == 'there'

    @patch('kotti.views.util.title_to_name')
    def test_find_name_uses_title_to_name(self, title_to_name):
        view = self.make()
        title_to_name.return_value = 'cafe'
        assert view.find_name({'title': 'Bar'}) == 'cafe'
        title_to_name.assert_called_with('Bar')

    @patch('kotti.views.util.disambiguate_name')
    def test_find_name_uses_disambiguate_name(self, disambiguate_name):
        view = self.make()
        view.context['bar'] = Dummy()
        disambiguate_name.return_value = 'othername'
        assert view.find_name({'title': 'Bar'}) == 'othername'
        disambiguate_name.assert_called_with('bar')

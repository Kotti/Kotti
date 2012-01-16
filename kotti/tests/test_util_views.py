import time

from mock import patch
from mock import MagicMock

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

class TestTemplateAPI(UnitTestBase):
    def _make(self, context=None, request=None, id=1, **kwargs):
        from kotti import DBSession
        from kotti.resources import Node
        from kotti.views.util import TemplateAPI

        if context is None:
            session = DBSession()
            context = session.query(Node).get(id)
        if request is None:
            request = DummyRequest()
        return TemplateAPI(context, request, **kwargs)

    def _create_contents(self, root):
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

    def test_page_title(self):
        api = self._make()
        api.context.title = u"Hello, world!"
        self.assertEqual(api.page_title, u"Hello, world! - Hello, world!")

        api = self._make()
        api.context.title = u"Hello, world!"
        api.site_title = u"Wasnhierlos"
        self.assertEqual(api.page_title, u"Hello, world! - Wasnhierlos")

    @patch('kotti.views.util.get_settings')
    def test_site_title(self, get_settings):
        get_settings.return_value = {'kotti.site_title': u'This is it.'}
        api = self._make()
        self.assertEqual(api.site_title, u'This is it.')

    def test_list_children(self):
        api = self._make() # the default context is root
        root = api.context
        self.assertEquals(len(api.list_children(root)), 0)

        # Now try it on a little graph:
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        self.assertEquals(api.list_children(root), [a])
        self.assertEquals(api.list_children(a), [aa, ab, ac])
        self.assertEquals(api.list_children(aca), [])

        # The 'list_children_go_up' function works slightly different:
        # it returns the parent's children if the context doesn't have
        # any.  Only the third case is gonna be different:
        self.assertEquals(api.list_children_go_up(root), (root, [a]))
        self.assertEquals(api.list_children_go_up(a), (a, [aa, ab, ac]))
        self.assertEquals(api.list_children_go_up(aca), (ac, [aca, acb]))

    def test_root(self):
        api = self._make()
        root = api.context
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        self.assertEquals(self._make().root, root)
        self.assertEquals(self._make(acb).root, root)

    def test_edit_links(self):
        from kotti.util import ViewLink

        api = self._make()
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
        api = self._make()
        self.assertEqual(api.edit_links, [open_link])

    def test_context_links(self):
        # 'context_links' returns a two-tuple of the form (siblings,
        # children), where the URLs point to edit pages:
        root = self._make().root
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        api = self._make(ac)
        siblings, children = api.context_links

        # Note how siblings don't include self (ac)
        self.assertEqual(
            [item['node'] for item in siblings],
            [aa, ab]
            )
        self.assertEqual(
            [item['node'] for item in children],
            [aca, acb]
            )

    def test_breadcrumbs(self):
        root = self._make().root
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        api = self._make(acb)
        breadcrumbs = api.breadcrumbs
        self.assertEqual(
            [item['node'] for item in breadcrumbs],
            [root, a, ac, acb]
            )

    @patch('kotti.views.util.view_permitted')
    def test_find_edit_view_not_permitted(self, view_permitted):
        view_permitted.return_value = False
        api = self._make()
        api.request.view_name = u'edit'
        assert api._find_edit_view(api.context) == u''

    @patch('kotti.views.util.view_permitted')
    def test_find_edit_view(self, view_permitted):
        view_permitted.return_value = True
        api = self._make()
        api.request.view_name = u'share'
        assert api._find_edit_view(api.context) == u'share'

    @patch('kotti.views.util.get_renderer')
    def test_macro(self, get_renderer):
        api = self._make()
        macro = api.macro('mypackage:mytemplate.pt')
        get_renderer.assert_called_with('mypackage:mytemplate.pt')
        assert get_renderer().implementation().macros['main'] == macro

    @patch('kotti.views.util.get_renderer')
    def test_macro_bare_with_master(self, get_renderer):
        # getting EDIT_MASTER when bare=True will return BARE_MASTER
        api = self._make(bare=True)
        macro = api.macro(api.EDIT_MASTER)
        get_renderer.assert_called_with(api.BARE_MASTER)
        assert get_renderer().implementation().macros['main'] == macro

    @patch('kotti.views.util.get_renderer')
    def test_macro_bare_without_master(self, get_renderer):
        # getting other templates when bare=True
        api = self._make(bare=True)
        macro = api.macro('mypackage:mytemplate.pt')
        get_renderer.assert_called_with('mypackage:mytemplate.pt')
        assert get_renderer().implementation().macros['main'] == macro

    def test_bare(self):
        # By default, no "bare" templates are used:
        api = self._make()
        self.assertEqual(api.bare, None)

        # We can ask for "bare" templates explicitely:
        api = self._make(bare=True)
        self.assertEqual(api.bare, True)

        # An XHR request will always result in bare master templates:
        request = DummyRequest()
        request.is_xhr = True
        api = self._make(request=request)
        self.assertEqual(api.bare, True)

        # unless overridden:
        api = self._make(request=request, bare=False)
        self.assertEqual(api.bare, False)

    def test_slots(self):
        from kotti.views.slots import register, RenderAboveContent
        def render_something(context, request):
            return u"Hello, %s!" % context.title
        register(RenderAboveContent, None, render_something)

        api = self._make()
        self.assertEqual(api.slots.abovecontent,
                         [u'Hello, %s!' % api.context.title])

        # Slot renderers may also return lists:
        def render_a_list(context, request):
            return [u"a", u"list"]
        register(RenderAboveContent, None, render_a_list)
        api = self._make()
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
        
        api = self._make()
        api.slots.belowcontent
        self.assertFalse(called)

        api.slots.abovecontent
        self.assertEquals(len(called), 1)
        api.slots.abovecontent
        self.assertEquals(len(called), 1)

    def test_slots_render_local_navigation(self):
        from kotti import DBSession
        from kotti.resources import Node
        from kotti.views.slots import render_local_navigation

        root = DBSession.query(Node).get(1)
        request = DummyRequest()
        a, aa, ab, ac, aca, acb = self._create_contents(root)
        self.assertEqual(render_local_navigation(root, request), None)
        self.assertNotEqual(render_local_navigation(a, request), None)
        self.assertEqual("ab" in render_local_navigation(a, request), True)
        ab.in_navigation = False
        self.assertEqual("ab" in render_local_navigation(a, request), False)

    def test_format_datetime(self):
        import datetime
        from babel.dates import format_datetime
        from babel.core import UnknownLocaleError
        api = self._make()
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
        api = self._make()
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
        api = self._make()
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
        api = self._make()
        self.assertEqual(api.render_view(), u'first')
        self.assertEqual(api.render_view('second'), u'second')
        self.assertEqual(
            api.render_view(context=api.context, request=api.request), u'first')

    def test_render_template(self):
        renderer = MagicMock()
        self.config.testing_add_renderer('my-rendererer', renderer)
        api = self._make()
        api.render_template('my-rendererer', some='variable')
        self.assertEqual(renderer.call_args[0][0], {'some': 'variable'})

    def test_get_type(self):
        from kotti.resources import Document
        api = self._make()
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

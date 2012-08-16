from unittest import TestCase
import warnings

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.request import Request
from pyramid.threadlocal import get_current_registry
from sqlalchemy import select
from zope.interface import implementedBy
from zope.interface import providedBy

from kotti.testing import TestingRootFactory
from kotti.testing import UnitTestBase
from kotti.testing import testing_db_url


def _includeme_login(config):
    config.add_view(
        _login_view,
        name='login',
        renderer='kotti:templates/login.pt',
        )


def _includeme_layout(config):
    # override edit master layout with view master layout
    config.override_asset(
        to_override='kotti:templates/edit/master.pt',
        override_with='kotti:templates/view/master.pt',
        )


def _login_view(request):
    return {}  # pragma: no cover


def _dummy_search(search_term, request):
    return u"Not found. Sorry!"


class TestApp(UnitTestBase):
    def required_settings(self):
        return {'sqlalchemy.url': testing_db_url(),
                'kotti.secret': 'dude'}

    def test_override_settings(self):
        from kotti import main
        from kotti import get_settings

        class MyType(object):
            pass

        def my_configurator(conf):
            conf['kotti.base_includes'] = ''
            conf['kotti.available_types'] = [MyType]

        settings = self.required_settings()
        settings['kotti.configurators'] = [my_configurator]
        main({}, **settings)

        self.assertEqual(get_settings()['kotti.base_includes'], [])
        self.assertEqual(get_settings()['kotti.available_types'], [MyType])

    def test_auth_policies_no_override(self):
        from kotti import main

        settings = self.required_settings()
        main({}, **settings)

        registry = get_current_registry()
        assert registry.queryUtility(IAuthenticationPolicy) is not None
        assert registry.queryUtility(IAuthorizationPolicy) is not None

    def test_auth_policies_override(self):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.authn_policy_factory'] = 'kotti.none_factory'
        settings['kotti.authz_policy_factory'] = 'kotti.none_factory'
        main({}, **settings)

        registry = get_current_registry()
        assert registry.queryUtility(IAuthenticationPolicy) is None
        assert registry.queryUtility(IAuthorizationPolicy) is None

    def test_asset_overrides(self):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.asset_overrides'] = 'pyramid:scaffold/ pyramid.fixers'
        main({}, **settings)

    def test_kotti_includes_deprecation_warning(self):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.includes'] = (
            'kotti.tests.test_app._includeme_layout')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            main({}, **settings)
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            msg = str(w[-1].message)
            assert "The 'kotti.includes' setting has been deprecated" in msg

    def test_kotti_includes_merged_to_pyramid_includes(self):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.includes'] = (
            'kotti.tests.test_app._includeme_login')

        app = main({}, **settings)
        assert (app.registry.settings['pyramid.includes'].strip() ==
                'kotti.tests.test_app._includeme_login')

        settings = self.required_settings()
        settings['pyramid.includes'] = (
            'kotti.tests.test_app._includeme_layout')
        settings['kotti.includes'] = (
            'kotti.tests.test_app._includeme_login')
        app = main({}, **settings)
        regsettings = app.registry.settings
        assert len(regsettings['pyramid.includes'].split()) == 2
        assert settings['kotti.includes'] in regsettings['pyramid.includes']

    def test_pyramid_includes_overrides_base_includes(self):
        from kotti import main
        from kotti.resources import get_root

        settings = self.required_settings()
        settings['pyramid.includes'] = (
            'kotti.tests.test_app._includeme_login')
        app = main({}, **settings)

        provides = [
            IViewClassifier,
            implementedBy(Request),
            providedBy(get_root()),
            ]
        view = app.registry.adapters.lookup(provides, IView, name='login')
        assert view.__module__ == __name__

    def test_use_tables(self):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.populators'] = ''
        settings['kotti.use_tables'] = 'principals'
        main({}, **settings)

    def test_root_factory(self):
        from kotti import main
        from kotti.resources import get_root

        settings = self.required_settings()
        settings['kotti.root_factory'] = (TestingRootFactory,)
        app = main({}, **settings)
        assert isinstance(get_root(), TestingRootFactory)
        assert isinstance(app.root_factory(), TestingRootFactory)

    def test_render_master_edit_template_minimal_root(self, settings=None):
        from kotti import main

        settings = settings or self.required_settings()
        settings['kotti.root_factory'] = (TestingRootFactory,)
        settings['kotti.site_title'] = 'My Site'
        app = main({}, **settings)

        request = Request.blank('/@@login')
        (status, headers, response) = request.call_application(app)
        assert status == '200 OK'

    def test_render_master_view_template_minimal_root(self):
        settings = self.required_settings()
        settings['pyramid.includes'] = (
            'kotti.tests.test_app._includeme_layout')
        return self.test_render_master_edit_template_minimal_root(settings)

    def test_setting_values_as_unicode(self):
        from kotti import get_settings
        from kotti import main

        settings = self.required_settings()
        settings['kotti.site_title'] = 'K\xc3\xb6tti'  # Kötti
        settings['kotti_foo.site_title'] = 'K\xc3\xb6tti'
        settings['foo.site_title'] = 'K\xc3\xb6tti'

        main({}, **settings)
        assert get_settings()['kotti.site_title'] == u'K\xf6tti'
        assert get_settings()['kotti_foo.site_title'] == u'K\xf6tti'
        assert get_settings()['foo.site_title'] == 'K\xc3\xb6tti'

    def test_search_content(self):
        from kotti import main
        from kotti.views.util import search_content

        settings = self.required_settings()
        settings['kotti.search_content'] = 'kotti.tests.test_app._dummy_search'
        main({}, **settings)
        assert search_content(u"Nuno") == u"Not found. Sorry!"

    def test_stamp_heads(self):
        from kotti import main
        from kotti import DBSession

        settings = self.required_settings()
        main({}, **settings)

        res = DBSession.execute(select(
            columns=['version_num'], from_obj=['kotti_alembic_version']))
        assert tuple(res)  # a version_num should exist


class TestGetVersion(TestCase):
    def test_it(self):
        from kotti import get_version
        assert isinstance(get_version(), str)

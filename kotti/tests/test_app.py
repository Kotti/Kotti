import warnings

from webob import Request

from kotti.testing import TestingRootFactory
from kotti.testing import UnitTestBase

class TestApp(UnitTestBase):
    def required_settings(self):
        return {'sqlalchemy.url': 'sqlite://',
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
        from pyramid.interfaces import IAuthenticationPolicy
        from pyramid.interfaces import IAuthorizationPolicy
        from pyramid.threadlocal import get_current_registry
        from kotti import main

        settings = self.required_settings()
        main({}, **settings)

        registry = get_current_registry()
        assert registry.queryUtility(IAuthenticationPolicy) != None
        assert registry.queryUtility(IAuthorizationPolicy) != None

    def test_auth_policies_override(self):
        from pyramid.interfaces import IAuthenticationPolicy
        from pyramid.interfaces import IAuthorizationPolicy
        from pyramid.threadlocal import get_current_registry
        from kotti import main

        settings = self.required_settings()
        settings['kotti.authn_policy_factory'] = 'kotti.none_factory'
        settings['kotti.authz_policy_factory'] = 'kotti.none_factory'
        main({}, **settings)

        registry = get_current_registry()
        assert registry.queryUtility(IAuthenticationPolicy) == None
        assert registry.queryUtility(IAuthorizationPolicy) == None

    def test_persistent_settings(self):
        from kotti import get_settings
        from kotti import get_version
        from kotti import DBSession
        from kotti.resources import Settings

        session = DBSession()
        [settings] = session.query(Settings).all()
        self.assertEqual(settings.data, {'kotti.db_version': get_version()})
        self.assertEqual(get_settings()['kotti.db_version'], get_version())
        settings.data['foo.bar'] = u'baz'
        self.assertEqual(get_settings()['foo.bar'], u'baz')

    def test_persistent_settings_add_new(self):
        from kotti import DBSession
        from kotti import get_settings
        from kotti.resources import Settings

        [settings] = DBSession.query(Settings).all()
        data = {'foo.bar': u'spam', 'kotti.db_version': u'next'}
        new_settings = settings.copy(data)
        DBSession.add(new_settings)
        self.assertEqual(get_settings()['foo.bar'], u'spam')
        self.assertEqual(get_settings()['kotti.db_version'], u'next')

    def test_asset_overrides(self):
        from kotti import main
        
        settings = self.required_settings()
        settings['kotti.asset_overrides'] = 'pyramid:scaffold/ pyramid.fixers'
        main({}, **settings)

    @staticmethod
    def _includeme_login(config):
        from kotti.resources import Node
        from kotti.views.login import login

        config.add_view(
            login,
            name='login',
            context=Node,
            renderer='kotti:templates/login.pt',
            )

    def test_kotti_includes_deprecation_warning(self):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.includes'] = (
            'kotti.tests.test_app.TestApp._includeme_layout')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            main({}, **settings)
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert 'Please set on ``pyramid.includes``' in str(w[-1].message)

    def test_kotti_includes_merged_to_pyramid_includes(self):
        from kotti import get_settings
        from kotti import main

        settings = self.required_settings()
        settings['kotti.includes'] = (
            'kotti.tests.test_app.TestApp._includeme_login')

        assert settings.get('pyramid.includes') is None
        main({}, **settings)
        assert get_settings()['pyramid.includes'] == settings['kotti.includes']

        settings = self.required_settings()
        settings['pyramid.includes'] = (
            'kotti.tests.test_app.TestApp._includeme_layout')
        settings['kotti.includes'] = (
            'kotti.tests.test_app.TestApp._includeme_login')
        main({}, **settings)
        assert len(get_settings()['pyramid.includes'].split(' ')) == 2
        assert settings['kotti.includes'] in get_settings()['pyramid.includes']

    def test_includes_overrides(self):
        from kotti import main

        settings = self.required_settings()
        settings['pyramid.includes'] = (
            'kotti.tests.test_app.TestApp._includeme_login')
        main({}, **settings)

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

    def test_render_master_edit_template_with_minimal_root(self, settings=None):
        from kotti import main

        settings = settings or self.required_settings()
        settings['kotti.root_factory'] = (TestingRootFactory,)
        settings['kotti.site_title'] = 'My Site'
        app = main({}, **settings)
        
        request = Request.blank('/@@login')
        (status, headers, response) = request.call_application(app)
        assert status == '200 OK'

    @staticmethod
    def _includeme_layout(config):
        # override edit master layout with view master layout
        config.override_asset(
            to_override='kotti:templates/edit/master.pt',
            override_with='kotti:templates/view/master.pt',
            ) 

    def test_render_master_view_template_with_minimal_root(self):
        settings = self.required_settings()
        settings['pyramid.includes'] = (
            'kotti.tests.test_app.TestApp._includeme_layout')
        return self.test_render_master_edit_template_with_minimal_root(settings)

    def test_setting_values_as_unicode(self):
        from kotti import get_settings
        from kotti import main

        settings = self.required_settings()
        settings['kotti.site_title'] = 'K\xc3\xb6tti' # Kötti

        main({}, **settings)
        self.assertEqual(get_settings()['kotti.site_title'], u'K\xf6tti')

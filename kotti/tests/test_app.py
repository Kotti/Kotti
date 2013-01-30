# -*- coding: utf-8 -*-

import warnings

from mock import patch, Mock
from pytest import raises

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
from kotti.testing import testing_db_url


# filter deprecation warnings for code that is still tested...
from warnings import filterwarnings
filterwarnings('ignore', "^The 'kotti.includes' setting")


class TestApp:

    def required_settings(self):
        return {'sqlalchemy.url': testing_db_url(),
                'kotti.secret': 'dude'}

    def test_override_settings(self, db_session):
        from kotti import main
        from kotti import get_settings

        class MyType(object):
            pass

        def my_configurator(conf):
            conf['kotti.base_includes'] = ''
            conf['kotti.available_types'] = [MyType]

        settings = self.required_settings()
        settings['kotti.configurators'] = [my_configurator]
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)

        assert get_settings()['kotti.base_includes'] == []
        assert get_settings()['kotti.available_types'] == [MyType]

    def test_auth_policies_no_override(self, db_session):
        from kotti import main

        settings = self.required_settings()
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)

        registry = get_current_registry()
        assert registry.queryUtility(IAuthenticationPolicy) is not None
        assert registry.queryUtility(IAuthorizationPolicy) is not None

    def test_auth_policies_override(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.authn_policy_factory'] = 'kotti.none_factory'
        settings['kotti.authz_policy_factory'] = 'kotti.none_factory'
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)

        registry = get_current_registry()
        assert registry.queryUtility(IAuthenticationPolicy) is None
        assert registry.queryUtility(IAuthorizationPolicy) is None

    def test_asset_overrides(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.asset_overrides'] = 'pyramid:scaffold/ pyramid.fixers'
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)

    def test_kotti_static_deprecated(self):
        with warnings.catch_warnings(record=True) as w:
            from kotti.static import edit_needed
            edit_needed  # pyflakes
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            msg = str(w[-1].message)
            assert "The module kotti.static has been moved to kotti.fanstatic as of Kotti" in msg

    def test_kotti_static_needed_deprecation_warning(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.static.view_needed'] = (' kotti.fanstatic.view_needed')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            with patch('kotti.resources.initialize_sql'):
                main({}, **settings)
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            msg = str(w[-1].message)
            assert "The 'kotti.static.view_needed' setting has been deprecated" in msg

    def test_kotti_static_needed_merged_to_kotti_fanstatic_needed(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.static.needed'] = 'kotti.fanstatic.edit_needed'

        with patch('kotti.resources.initialize_sql'):
            app = main({}, **settings)

        groups = app.registry.settings['kotti.fanstatic.view_needed']
        resource_names = [[r.relpath for r in group.resources] for group in groups]
        resource_names = [name for names in resource_names for name in names]
        assert 'view.css' in resource_names

        settings = self.required_settings()
        settings['kotti.fanstatic.view_needed'] = 'kotti.fanstatic.view_needed'
        settings['kotti.static.view_needed'] = ' kotti.fanstatic.edit_needed'
        with warnings.catch_warnings(record=True):
            with patch('kotti.resources.initialize_sql'):
                app = main({}, **settings)
        regsettings = app.registry.settings

        assert len(regsettings['kotti.fanstatic.view_needed']) == 2

        with raises(KeyError):
            regsettings['kotti.static.view_needed']

        groups = regsettings['kotti.fanstatic.view_needed']
        resource_names = [[r.relpath for r in group.resources] for group in groups]
        resource_names = [name for names in resource_names for name in names]
        assert 'edit.css' in resource_names

    def test_kotti_includes_deprecation_warning(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.includes'] = ('kotti.testing.includeme_layout')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            with patch('kotti.resources.initialize_sql'):
                main({}, **settings)
            assert len(w) == 1
            assert issubclass(w[-1].category, DeprecationWarning)
            msg = str(w[-1].message)
            assert "The 'kotti.includes' setting has been deprecated" in msg

    def test_kotti_includes_merged_to_pyramid_includes(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.includes'] = ('kotti.testing.includeme_login')

        with patch('kotti.resources.initialize_sql'):
            app = main({}, **settings)
        assert (app.registry.settings['pyramid.includes'].strip() ==
                'kotti.testing.includeme_login')

        settings = self.required_settings()
        settings['pyramid.includes'] = ('kotti.testing.includeme_layout')
        settings['kotti.includes'] = ('kotti.testing.includeme_login')
        with patch('kotti.resources.initialize_sql'):
            app = main({}, **settings)
        regsettings = app.registry.settings
        assert len(regsettings['pyramid.includes'].split()) == 2
        assert settings['kotti.includes'] in regsettings['pyramid.includes']

    def test_pyramid_includes_overrides_base_includes(self, root):
        from kotti import main

        settings = self.required_settings()
        settings['pyramid.includes'] = ('kotti.testing.includeme_login')
        with patch('kotti.resources.initialize_sql'):
            app = main({}, **settings)

        provides = [
            IViewClassifier,
            implementedBy(Request),
            providedBy(root),
            ]
        view = app.registry.adapters.lookup(provides, IView, name='login')
        assert view.__module__ == 'kotti.testing'

    def test_use_tables(self, db_session):
        from kotti import main

        settings = self.required_settings()
        settings['kotti.populators'] = ''
        settings['kotti.use_tables'] = 'principals'
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)

    def test_root_factory(self, db_session):
        from kotti import main
        from kotti.resources import get_root    # the `root` fixture doesn't work here

        settings = self.required_settings()
        settings['kotti.root_factory'] = (TestingRootFactory,)
        with patch('kotti.resources.initialize_sql'):
            app = main({}, **settings)
        assert isinstance(get_root(), TestingRootFactory)
        assert isinstance(app.root_factory(), TestingRootFactory)

    def test_render_master_edit_template_minimal_root(self, settings=None):
        from kotti import main

        settings = settings or self.required_settings()
        settings['kotti.root_factory'] = (TestingRootFactory,)
        settings['kotti.site_title'] = 'My Site'
        with patch('kotti.resources.initialize_sql'):
            app = main({}, **settings)

        request = Request.blank('/@@login')
        (status, headers, response) = request.call_application(app)
        assert status == '200 OK'

    def test_render_master_view_template_minimal_root(self, db_session):
        settings = self.required_settings()
        settings['pyramid.includes'] = ('kotti.testing.includeme_layout')
        return self.test_render_master_edit_template_minimal_root(settings)

    def test_setting_values_as_unicode(self, db_session):
        from kotti import get_settings
        from kotti import main

        settings = self.required_settings()
        settings['kotti.site_title'] = 'K\xc3\xb6tti'  # Kötti
        settings['kotti_foo.site_title'] = 'K\xc3\xb6tti'
        settings['foo.site_title'] = 'K\xc3\xb6tti'

        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)
        assert get_settings()['kotti.site_title'] == u'K\xf6tti'
        assert get_settings()['kotti_foo.site_title'] == u'K\xf6tti'
        assert get_settings()['foo.site_title'] == 'K\xc3\xb6tti'

    def test_search_content(self, db_session):
        from kotti import main
        from kotti.views.util import search_content

        settings = self.required_settings()
        settings['kotti.search_content'] = 'kotti.testing.dummy_search'
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)
        assert search_content(u"Nuno") == u"Not found. Sorry!"

    def test_stamp_heads(self, db_session, connection):
        from kotti import main

        settings = self.required_settings()
        engine = connection.engine
        engine.table_names = Mock(return_value=[])
        with patch('kotti.engine_from_config', return_value=engine):
            with patch('kotti.resources.metadata'):
                main({}, **settings)

        res = db_session.execute(select(
            columns=['version_num'], from_obj=['kotti_alembic_version']))
        assert tuple(res)  # a version_num should exist


class TestGetVersion:
    def test_it(self):
        from kotti import get_version
        assert isinstance(get_version(), str)

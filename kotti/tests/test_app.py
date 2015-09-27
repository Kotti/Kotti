# -*- coding: utf-8 -*-

from mock import patch, Mock

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.interfaces import IView
from pyramid.interfaces import IViewClassifier
from pyramid.request import Request
from pyramid.threadlocal import get_current_registry
from sqlalchemy import column
from sqlalchemy import select
from sqlalchemy import table
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
        settings['kotti.asset_overrides'] = 'pyramid:scaffold/'
        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)

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
        # the `root` fixture doesn't work here
        from kotti.resources import get_root

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

    def test_default_filedepot(self, db_session):
        from kotti import main
        from depot.manager import DepotManager

        settings = self.required_settings()

        with patch('kotti.resources.initialize_sql'):
            main({}, **settings)
        assert DepotManager.get().__class__.__name__ == 'DBFileStorage'

    def test_configure_filedepot(self, no_filedepots):
        from depot.manager import DepotManager
        from kotti.filedepot import configure_filedepot
        from kotti import tests

        tests.TFS1 = Mock(return_value=Mock(marker="TFS1"))
        tests.TFS2 = Mock(return_value=Mock(marker="TFS2"))

        settings = {
            'kotti.depot.0.backend': 'kotti.tests.TFS1',
            'kotti.depot.0.name': 'localfs',
            'kotti.depot.0.location': '/tmp',
            'kotti.depot.1.backend': 'kotti.tests.TFS2',
            'kotti.depot.1.uri': 'mongo://',
            'kotti.depot.1.name': 'mongo',
        }

        configure_filedepot(settings)

        assert DepotManager.get().marker == 'TFS1'
        assert DepotManager.get('localfs').marker == 'TFS1'
        assert DepotManager.get('mongo').marker == 'TFS2'

        tests.TFS1.assert_called_with(location='/tmp')
        tests.TFS2.assert_called_with(uri='mongo://')

        del tests.TFS1
        del tests.TFS2

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
            columns=[column('version_num')],
            from_obj=[table('kotti_alembic_version')]))
        assert tuple(res)  # a version_num should exist


class TestGetVersion:
    def test_it(self):
        from kotti import get_version
        assert isinstance(get_version(), str)

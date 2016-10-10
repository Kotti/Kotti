# -*- coding: utf-8 -*-

"""
Inheritance Diagram
-------------------

.. inheritance-diagram:: kotti.testing
"""

import os
from os.path import join, dirname
from unittest import TestCase
from warnings import catch_warnings

import transaction
from pyramid import testing
from pyramid.events import NewResponse
from pyramid.interfaces import ILocation
from pyramid.security import ALL_PERMISSIONS
from pytest import mark
from zope.interface import implementer

# re-enable deprecation warnings during test runs
# however, let the `ImportWarning` produced by Babel's
# `localedata.py` vs `localedata/` show up once...
with catch_warnings():
    from babel import localedata
    import compiler
    localedata, compiler    # make pyflakes happy... :p


# py.test markers (see http://pytest.org/latest/example/markers.html)
user = mark.user


BASE_URL = 'http://localhost:6543'


class Dummy(dict):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class DummyRequest(testing.DummyRequest):
    is_xhr = False
    POST = dict()
    user = None
    referrer = None

    @staticmethod
    def is_response(ob):
        return (hasattr(ob, 'app_iter') and hasattr(ob, 'headerlist') and
                hasattr(ob, 'status'))


def asset(name):
    import kotti
    return open(join(dirname(kotti.__file__), 'tests', name), 'rb')


def includeme_login(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.add_view(
        login_view,
        name='login',
        renderer='kotti:templates/login.pt')


def includeme_layout(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    # override edit master layout with view master layout

    config.override_asset(
        to_override='kotti:templates/edit/master.pt',
        override_with='kotti:templates/view/master.pt')


def login_view(request):
    return {}


def dummy_search(search_term, request):
    return u"Not found. Sorry!"


def testing_db_url():
    return os.environ.get('KOTTI_TEST_DB_STRING', 'sqlite://')


def _initTestingDB():
    from sqlalchemy import create_engine
    from kotti import get_settings
    from kotti.resources import initialize_sql

    database_url = testing_db_url()
    get_settings()['sqlalchemy.url'] = database_url
    session = initialize_sql(create_engine(database_url), drop_all=True)
    return session


def _populator():
    from kotti import DBSession
    from kotti.resources import Document
    from kotti.populate import populate

    populate()
    for doc in DBSession.query(Document)[1:]:
        DBSession.delete(doc)
    transaction.commit()


def _turn_warnings_into_errors():  # pragma: no cover
    # turn all warnings into errors, but let the `ImportWarning`
    # produced by Babel's `localedata.py` vs `localedata/` show up once...
    from babel import localedata
    localedata  # make pyflakes happy... :p
    from warnings import filterwarnings
    filterwarnings("error")


def setUp(init_db=True, **kwargs):
    # _turn_warnings_into_errors()

    from kotti import _resolve_dotted
    from kotti import conf_defaults

    tearDown()
    settings = conf_defaults.copy()
    settings['kotti.secret'] = 'secret'
    settings['kotti.secret2'] = 'secret2'
    settings['kotti.populators'] = 'kotti.testing._populator'
    settings.update(kwargs.get('settings', {}))
    settings = _resolve_dotted(settings)
    kwargs['settings'] = settings
    config = testing.setUp(**kwargs)
    config.add_default_renderers()

    if init_db:
        _initTestingDB()

    transaction.begin()
    return config


def tearDown():
    from depot.manager import DepotManager
    from kotti import events
    from kotti import security
    from kotti.message import _inject_mailer

    # These should arguable use the configurator, so they don't need
    # to be torn down separately:
    events.clear()
    security.reset()

    _inject_mailer[:] = []
    transaction.abort()
    DepotManager._clear()
    testing.tearDown()


class UnitTestBase(TestCase):
    def setUp(self, **kwargs):
        self.config = setUp(**kwargs)

    def tearDown(self):
        tearDown()


class EventTestBase(TestCase):
    def setUp(self, **kwargs):
        super(EventTestBase, self).setUp(**kwargs)
        self.config.include('kotti.events')

# Functional ----


def _functional_includeme(config):
    from kotti import DBSession

    def expire(event):
        DBSession.flush()
        DBSession.expire_all()

    config.add_subscriber(expire, NewResponse)


def _zope_testbrowser_pyquery(self):
    from pyquery import PyQuery
    return PyQuery(
        self.contents.replace('xmlns="http://www.w3.org/1999/xhtml', ''))


def setUpFunctional(global_config=None, **settings):
    from kotti import main
    from zope.testbrowser.wsgi import Browser
    from webtest import TestApp

    tearDown()

    _settings = {
        'sqlalchemy.url': testing_db_url(),
        'kotti.secret': 'secret',
        'kotti.site_title': 'Website des Kottbusser Tors',  # for mailing
        'kotti.populators': 'kotti.testing._populator',
        'mail.default_sender': 'kotti@localhost',
        'pyramid.includes': 'kotti.testing._functional_includeme',
        }
    _settings.update(settings)

    host, port = BASE_URL.split(':')[-2:]
    app = main({}, **_settings)
    Browser.pyquery = property(_zope_testbrowser_pyquery)

    return dict(
        Browser=lambda: Browser(
            'http://{}:{}/'.format(host[2:], int(port)),
            wsgi_app=app),
        browser=Browser(
            'http://{}:{}/'.format(host[2:], int(port)),
            wsgi_app=app),
        test_app=TestApp(app),
        )


class FunctionalTestBase(TestCase):
    BASE_URL = BASE_URL

    def setUp(self, **kwargs):
        self.__dict__.update(setUpFunctional(**kwargs))

    def tearDown(self):
        tearDown()

    def login(self, login=u'admin', password=u'secret'):
        return self.test_app.post(
            '/@@login',
            {'login': login, 'password': password, 'submit': 'submit'},
            status=302,
            )


@implementer(ILocation)
class RootFactory(dict):
    __name__ = ''  # root is required to have an empty name!
    __parent__ = None
    __acl__ = [('Allow', 'role:admin', ALL_PERMISSIONS)]

    def __init__(self, request):
        super(RootFactory, self).__init__()


def dummy_view(context, request):
    return {}


def include_testing_view(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.add_view(
        dummy_view,
        context=RootFactory,
        renderer='kotti:tests/testing_view.pt',
        )

    config.add_view(
        dummy_view,
        name='secured',
        permission='view',
        context=RootFactory,
        renderer='kotti:tests/testing_view.pt',
        )


def setUpFunctionalStrippedDownApp(global_config=None, **settings):
    # An app that doesn't use Nodes at all
    _settings = {
        'kotti.base_includes': (
            'kotti kotti.views kotti.views.login kotti.views.users '
            'kotti.views.view'),
        'kotti.use_tables': 'principals',
        'kotti.populators': 'kotti.populate.populate_users',
        'pyramid.includes': 'kotti.testing.include_testing_view',
        'kotti.root_factory': 'kotti.testing.RootFactory',
        'kotti.site_title': 'My Stripped Down Kotti',
        }
    _settings.update(settings)

    return setUpFunctional(global_config, **_settings)


def registerDummyMailer():
    from pyramid_mailer.mailer import DummyMailer
    from kotti.message import _inject_mailer

    mailer = DummyMailer()
    _inject_mailer.append(mailer)
    return mailer


# set up deprecation warnings
from zope.deprecation.deprecation import deprecated  # noqa
for item in UnitTestBase, EventTestBase, FunctionalTestBase, _initTestingDB:
    name = getattr(item, '__name__', item)
    deprecated(name, 'Unittest-style tests are deprecated as of Kotti 0.7. '
               'Please use pytest function arguments instead.')

TestingRootFactory = RootFactory
deprecated('TestingRootFactory',
           "TestingRootFactory has been renamed to RootFactory and will be no "
           "longer available starting with Kotti 2.0.0.")

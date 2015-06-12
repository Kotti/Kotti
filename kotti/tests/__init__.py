# -*- coding: utf-8 -*-

"""

Fixture dependencies
--------------------

.. graphviz::

   digraph kotti_fixtures {
      "allwarnings";
      "mock_filedepot";
      "app" -> "webtest";
      "config" -> "db_session";
      "config" -> "dummy_request";
      "config" -> "events";
      "config" -> "workflow";
      "connection" -> "content";
      "connection" -> "db_session";
      "content" -> "db_session";
      "custom_settings" -> "connection";
      "custom_settings" -> "unresolved_settings";
      "db_session" -> "app";
      "db_session" -> "browser";
      "db_session" -> "root";
      "db_session" -> "filedepot";
      "dummy_mailer" -> "app";
      "dummy_mailer";
      "events" -> "app";
      "settings" -> "config";
      "settings" -> "content";
      "setup_app" -> "app";
      "setup_app" -> "browser";
      "unresolved_settings" -> "settings";
      "unresolved_settings" -> "setup_app";
      "workflow" -> "app";
   }

"""

# public pytest fixtures

import warnings

from pytest import fixture
from mock import MagicMock

from datetime import datetime


@fixture
def allwarnings(request):
    save_filters = warnings.filters[:]
    warnings.filters[:] = []

    def restore():
        warnings.filters[:] = save_filters

    request.addfinalizer(restore)


@fixture(scope='session')
def custom_settings():
    """ This is a dummy fixture meant to be overriden in add on package's
    ``conftest.py``.  It can be used to inject arbitrary settings for third
    party test suites.  The default settings dictionary will be updated
    with the dictionary returned by this fixture.

    This is also a good place to import your add on's ``resources`` module to
    have the corresponding tables created during ``create_all()`` in
    :func:`kotti.tests.content`.

    :result: settings
    :rtype: dict
    """

    return {}


@fixture(scope='session')
def unresolved_settings(custom_settings):
    from kotti import conf_defaults
    from kotti.testing import testing_db_url
    settings = conf_defaults.copy()
    settings['kotti.secret'] = 'secret'
    settings['kotti.secret2'] = 'secret2'
    settings['kotti.populators'] = 'kotti.testing._populator'
    settings['sqlalchemy.url'] = testing_db_url()
    settings.update(custom_settings)
    return settings


@fixture(scope='session')
def settings(unresolved_settings):
    from kotti import _resolve_dotted
    return _resolve_dotted(unresolved_settings)


@fixture
def config(request, settings):
    """ returns a Pyramid `Configurator` object initialized
        with Kotti's default (test) settings.
    """
    from pyramid import testing
    from kotti import security
    config = testing.setUp(settings=settings)
    config.include('pyramid_chameleon')
    config.add_default_renderers()
    request.addfinalizer(security.reset)
    request.addfinalizer(testing.tearDown)
    return config


@fixture(scope='session')
def connection(custom_settings):
    """ sets up a SQLAlchemy engine and returns a connection to the database.
    The connection string used for testing can be specified via the
    ``KOTTI_TEST_DB_STRING`` environment variable.  The ``custom_settings``
    fixture is needed to allow users to import their models easily instead of
    having to override the ``connection``.
    """
    # the following setup is based on `kotti.resources.initialize_sql`,
    # except that it explicitly binds the session to a specific connection
    # enabling us to use savepoints independent from the orm, thus allowing
    # to `rollback` after using `transaction.commit`...
    from sqlalchemy import create_engine
    from kotti import DBSession
    from kotti import metadata
    from kotti.resources import _adjust_for_engine
    from kotti.testing import testing_db_url
    engine = create_engine(testing_db_url())
    _adjust_for_engine(engine)
    connection = engine.connect()
    DBSession.registry.clear()
    DBSession.configure(bind=connection)
    metadata.bind = engine
    return connection


@fixture(scope='session')
def content(connection, settings):
    """ sets up some default content using Kotti's testing populator.
    """
    from transaction import commit
    from kotti import metadata
    from kotti.resources import get_root
    metadata.drop_all(connection.engine)
    metadata.create_all(connection.engine)
    # to create the default content with the correct workflow state
    # the workflow must be initialized first;  please note that these
    # settings won't persist, though;  use the `workflow` fixture if needed
    from zope.configuration import xmlconfig
    import kotti
    xmlconfig.file('workflow.zcml', kotti, execute=True)
    for populate in settings['kotti.populators']:
        populate()

    # We set the path here since it's required for some integration
    # tests, and because the 'content' fixture does not depend on
    # 'event' and therefore the event handlers aren't fired for root
    # otherwise:
    get_root().path = u'/'
    commit()


@fixture
def db_session(config, content, connection, request):
    """ returns a db session object and sets up a db transaction
        savepoint, which will be rolled back after the test.
    """

    from transaction import abort
    trans = connection.begin()          # begin a non-orm transaction
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)
    from kotti import DBSession
    return DBSession()


@fixture
def dummy_request(config, request, monkeypatch):
    """ returns a dummy request object after registering it as
        the currently active request.  This is needed when
        `pyramid.threadlocal.get_current_request` is used.
    """

    from kotti.testing import DummyRequest

    if 'user' in request.keywords:
        monkeypatch.setattr(
            DummyRequest,
            "authenticated_userid",
            request.keywords['user'].args[0])

    config.manager.get()['request'] = dummy_request = DummyRequest()

    return dummy_request


@fixture
def dummy_mailer(monkeypatch):
    from pyramid_mailer.mailer import DummyMailer

    mailer = DummyMailer()
    monkeypatch.setattr('kotti.message.get_mailer', lambda: mailer)
    return mailer


@fixture
def events(config, request):
    """ sets up Kotti's default event handlers.
    """
    from kotti.events import clear
    config.include('kotti.events')
    request.addfinalizer(clear)
    return config


@fixture
def setup_app(unresolved_settings):
    from kotti import base_configure
    config = base_configure({}, **unresolved_settings)
    return config.make_wsgi_app()


@fixture
def app(workflow, db_session, dummy_mailer, events, setup_app):
    return setup_app


@fixture
def browser(db_session, request, setup_app):
    """ returns an instance of `zope.testbrowser`.  The `kotti.testing.user`
        pytest marker (or `pytest.mark.user`) can be used to pre-authenticate
        the browser with the given login name: `@user('admin')`.
    """
    from wsgi_intercept import add_wsgi_intercept, zope_testbrowser
    from kotti.testing import BASE_URL
    host, port = BASE_URL.split(':')[-2:]
    add_wsgi_intercept(host[2:], int(port), lambda: setup_app)
    browser = zope_testbrowser.WSGI_Browser(BASE_URL + '/')
    if 'user' in request.keywords:
        # set auth cookie directly on the browser instance...
        from pyramid.security import remember
        from pyramid.testing import DummyRequest
        login = request.keywords['user'].args[0]
        environ = dict(HTTP_HOST=host[2:])
        for _, value in remember(DummyRequest(environ=environ), login):
            cookie, _ = value.split(';', 1)
            name, value = cookie.split('=')
            if name in browser.cookies:
                del browser.cookies[name]
            browser.cookies.create(name, value.strip('"'), path='/')
    return browser


@fixture
def root(db_session):
    """ returns Kotti's 'root' node.
    """
    from kotti.resources import get_root
    return get_root()


@fixture
def webtest(app, monkeypatch, request):
    from webtest import TestApp
    if 'user' in request.keywords:
        login = request.keywords['user'].args[0]
        monkeypatch.setattr(
            "pyramid.authentication."
            "AuthTktAuthenticationPolicy.unauthenticated_userid",
            lambda self, req: login)
    return TestApp(app)


@fixture
def workflow(config):
    """ loads and activates Kotti's default workflow rules.
    """
    from zope.configuration import xmlconfig
    import kotti
    xmlconfig.file('workflow.zcml', kotti, execute=True)


class TestStorage:
    def __init__(self):
        self._storage = {}
        self._storage.setdefault(0)

    def get(self, id):
        info = self._storage[id]

        from StringIO import StringIO

        f = MagicMock(wraps=StringIO(info['content']))
        f.seek(0)
        f.public_url = ''
        f.filename = info['filename']
        f.content_type = info['content_type']
        f.content_length = len(info['content'])
        # needed to make JSON serializable, Mock objects are not
        f.last_modified = datetime(2012, 12, 30)

        return f

    def create(self, content, filename=None, content_type=None):
        _id = max(self._storage) + 1
        filename = filename or getattr(content, 'filename', None)
        content_type = content_type or getattr(content, 'type', None)
        if not isinstance(content, str):
            content = content.file.read()
        self._storage[_id] = {'content': content,
                              'filename': filename,
                              'content_type': content_type}
        return _id

    def delete(self, id):
        del self._storage[int(id)]


@fixture
def mock_filedepot(request):
    """ Configures a mock depot store for :class:`depot.manager.DepotManager`

    This filedepot is not integrated with dbsession.
    Can be used in simple, standalone unit tests.
    """
    from depot.manager import DepotManager

    _old_depots = DepotManager._depots
    _old_default_depot = DepotManager._default_depot
    DepotManager._depots = {
        'mockdepot': MagicMock(wraps=TestStorage())
    }
    DepotManager._default_depot = 'mockdepot'

    def restore():
        DepotManager._depots = _old_depots
        DepotManager._default_depot = _old_default_depot

    request.addfinalizer(restore)


@fixture
def filedepot(db_session, request):
    """ Configures a dbsession integrated mock depot store for
    :class:`depot.manager.DepotManager`
    """
    from depot.manager import DepotManager

    _old_depots = DepotManager._depots
    _old_default_depot = DepotManager._default_depot
    DepotManager._depots = {
        'filedepot': MagicMock(wraps=TestStorage())
    }
    DepotManager._default_depot = 'filedepot'

    def restore():
        db_session.rollback()
        DepotManager._depots = _old_depots
        DepotManager._default_depot = _old_default_depot

    request.addfinalizer(restore)


@fixture
def no_filedepots(db_session, request):
    """ A filedepot fixture to empty and then restore DepotManager configuration
    """
    from depot.manager import DepotManager

    _old_depots = DepotManager._depots
    _old_default_depot = DepotManager._default_depot

    DepotManager._depots = {}
    DepotManager._default_depot = None

    def restore():
        db_session.rollback()
        DepotManager._depots = _old_depots
        DepotManager._default_depot = _old_default_depot

    request.addfinalizer(restore)

# public pytest fixtures

from pytest import fixture


def settings():
    from kotti import _resolve_dotted
    from kotti import conf_defaults
    settings = conf_defaults.copy()
    settings['kotti.secret'] = 'secret'
    settings['kotti.secret2'] = 'secret2'
    settings['kotti.populators'] = 'kotti.testing._populator'
    _resolve_dotted(settings)
    return settings


@fixture
def config(request):
    """ returns a Pyramid `Configurator` object initialized
        with Kotti's default (test) settings.
    """
    from pyramid.config import DEFAULT_RENDERERS
    from pyramid import testing
    from kotti import security
    config = testing.setUp(settings=settings())
    for name, renderer in DEFAULT_RENDERERS:
        config.add_renderer(name, renderer)
    request.addfinalizer(security.reset)
    request.addfinalizer(testing.tearDown)
    return config


@fixture(scope='session')
def connection():
    """ sets up a SQLAlchemy engine and returns a connection
        to the database.  The connection string used for testing
        can be specified via the `KOTTI_TEST_DB_STRING` environment
        variable.
    """
    # the following setup is based on `kotti.resources.initialize_sql`,
    # except that it explicitly binds the session to a specific connection
    # enabling us to use savepoints independent from the orm, thus allowing
    # to `rollback` after using `transaction.commit`...
    from sqlalchemy import create_engine
    from kotti.testing import testing_db_url
    from kotti import metadata, DBSession
    engine = create_engine(testing_db_url())
    connection = engine.connect()
    DBSession.registry.clear()
    DBSession.configure(bind=connection)
    metadata.bind = engine
    return connection


@fixture(scope='session')
def content(connection):
    """ sets up some default content using Kotti's testing populator.
    """
    from transaction import commit
    from kotti import metadata
    metadata.drop_all(connection.engine)
    metadata.create_all(connection.engine)
    # to create the default content with the correct workflow state
    # the workflow must be initialized first;  please note that these
    # settings won't persist, though;  use the `workflow` fixture if needed
    from zope.configuration import xmlconfig
    import kotti
    xmlconfig.file('workflow.zcml', kotti, execute=True)
    for populate in settings()['kotti.populators']:
        populate()
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
def dummy_request(config):
    """ returns a dummy request object after registering it as
        the currently active request.  This is needed when
        `pyramid.threadlocal.get_current_request` is used.
    """
    from kotti.testing import DummyRequest
    config.manager.get()['request'] = request = DummyRequest()
    return request


@fixture
def events(config, request):
    """ sets up Kotti's default event handlers.
    """
    from kotti.events import clear
    config.include('kotti.events')
    request.addfinalizer(clear)
    return config


def setup_app():
    from kotti import base_configure
    return base_configure({}, **settings()).make_wsgi_app()


@fixture
def browser(db_session, request):
    """ returns an instance of `zope.testbrowser`.  The `kotti.testing.user`
        pytest marker (or `pytest.mark.user`) can be used to pre-authenticate
        the browser with the given login name: `@user('admin')`.
    """
    from wsgi_intercept import add_wsgi_intercept, zope_testbrowser
    from kotti.testing import BASE_URL
    host, port = BASE_URL.split(':')[-2:]
    add_wsgi_intercept(host[2:], int(port), setup_app)
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
def workflow(config):
    """ loads and activates Kotti's default workflow rules.
    """
    from zope.configuration import xmlconfig
    import kotti
    xmlconfig.file('workflow.zcml', kotti, execute=True)

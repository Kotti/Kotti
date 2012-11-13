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
    # the following setup is based on `kotti.resources.initialize_sql`,
    # except that it explicitly binds the session to a specific connection
    # enabling us to use savepoints independent from the orm, thus allowing
    # to `rollback` after using `transaction.commit`...
    from transaction import commit
    from sqlalchemy import create_engine
    from kotti.testing import testing_db_url
    from kotti import metadata, DBSession
    engine = create_engine(testing_db_url())
    connection = engine.connect()
    DBSession.registry.clear()
    DBSession.configure(bind=connection)
    metadata.bind = engine
    metadata.drop_all(engine)
    metadata.create_all(engine)
    for populate in settings()['kotti.populators']:
        populate()
    commit()
    return connection


@fixture
def db_session(config, connection, request):
    from transaction import abort
    trans = connection.begin()          # begin a non-orm transaction
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)
    from kotti import DBSession
    return DBSession()


@fixture
def dummy_request(config):
    from kotti.testing import DummyRequest
    config.manager.get()['request'] = request = DummyRequest()
    return request


@fixture
def events(config, request):
    from kotti.events import clear
    config.include('kotti.events')
    request.addfinalizer(clear)
    return config


def setup_app():
    from mock import patch
    from kotti import main
    with patch('kotti.resources.initialize_sql'):
        with patch('kotti.engine_from_config'):
            app = main({}, **settings())
    return app


@fixture
def app(db_session):
    from webtest import TestApp
    return TestApp(setup_app())


@fixture
def browser(db_session, request):
    from wsgi_intercept import add_wsgi_intercept, zope_testbrowser
    add_wsgi_intercept('example.com', 80, app)
    browser = zope_testbrowser.WSGI_Browser('http://example.com/')
    if 'user' in request.keywords:
        # set auth cookie directly on the browser instance...
        from pyramid.security import remember
        from pyramid.testing import DummyRequest
        login = request.keywords['user'].args[0]
        environ = dict(HTTP_HOST='example.com')
        for _, value in remember(DummyRequest(environ=environ), login):
            cookie, _ = value.split(';', 1)
            name, value = cookie.split('=')
            if name in browser.cookies:
                del browser.cookies[name]
            browser.cookies.create(name, value.strip('"'), path='/')
    return browser


@fixture
def extra_principals(db_session):
    from kotti.security import get_principals
    P = get_principals()
    P[u'bob'] = dict(name=u'bob', title=u"Bob")
    P[u'frank'] = dict(name=u'frank', title=u"Frank")
    P[u'group:bobsgroup'] = dict(name=u'group:bobsgroup', title=u"Bob's Group")
    P[u'group:franksgroup'] = dict(name=u'group:franksgroup',
        title=u"Frank's Group")

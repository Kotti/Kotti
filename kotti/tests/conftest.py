

def test_settings():
    from kotti import _resolve_dotted
    from kotti import conf_defaults
    settings = conf_defaults.copy()
    settings['kotti.secret'] = 'secret'
    settings['kotti.secret2'] = 'secret2'
    settings['kotti.populators'] = 'kotti.testing._populator'
    _resolve_dotted(settings)
    return settings


def pytest_funcarg__config(request):
    from pyramid.config import DEFAULT_RENDERERS
    from pyramid import testing
    from kotti import security

    def teardown(config):
        security.reset()
        testing.tearDown()
    config = request.cached_setup(
        setup=lambda: testing.setUp(settings=test_settings()),
        teardown=teardown, scope='function')
    for name, renderer in DEFAULT_RENDERERS:
        config.add_renderer(name, renderer)
    return config


def pytest_funcarg__connection(request):
    # the following setup is based on `kotti.resources.initialize_sql`,
    # except that it explicitly binds the session to a specific connection
    # enabling us to use savepoints independent from the orm, thus allowing
    # to `rollback` after using `transaction.commit`...
    def setup():
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
        for populate in test_settings()['kotti.populators']:
            populate()
        commit()
        return connection
    return request.cached_setup(setup=setup, scope='session')


def pytest_funcarg__db_session(request):
    from transaction import abort
    request.getfuncargvalue('config')
    connection = request.getfuncargvalue('connection')
    trans = connection.begin()          # begin a non-orm transaction
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)
    from kotti import DBSession
    return DBSession()


def pytest_funcarg__request(request):
    from kotti.testing import DummyRequest
    config = request.getfuncargvalue('config')
    config.manager.get()['request'] = request = DummyRequest()
    return request


def pytest_funcarg__events(request):
    from kotti.events import clear
    config = request.getfuncargvalue('config')
    config.include('kotti.events')
    request.addfinalizer(clear)
    return config


def app():
    from mock import patch
    from kotti import main
    with patch('kotti.resources.initialize_sql'):
        with patch('kotti.engine_from_config'):
            app = main({}, **test_settings())
    return app


def pytest_funcarg__browser(request):
    def setup():
        from wsgi_intercept import add_wsgi_intercept, zope_testbrowser
        add_wsgi_intercept('example.com', 80, app)
        return zope_testbrowser.WSGI_Browser('http://example.com/')
    request.getfuncargvalue('db_session')   # db usually needs a rollback
    browser = request.cached_setup(setup=setup, scope='function')
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

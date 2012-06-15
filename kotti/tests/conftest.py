

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
    from pyramid.testing import setUp, tearDown
    config = request.cached_setup(
        setup=lambda: setUp(settings=test_settings()),
        teardown=tearDown, scope='function')
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
    config = request.getfuncargvalue('config')
    config.include('kotti.events')
    return config

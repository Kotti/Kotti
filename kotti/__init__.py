from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.util import DottedNameResolver

class Configuration(dict):
    """A dict that can resolve dotted names to Python objects the
    first time they're accessed.
    """
    def __init__(self, d, dotted_names):
        super(Configuration, self).__init__(d)
        self.dotted_names = dotted_names

    def __getitem__(self, key):
        value = super(Configuration, self).__getitem__(key)
        if key in self.dotted_names and isinstance(value, basestring):
            values = []
            for dottedname in value.split():
                values.append(DottedNameResolver(None).resolve(dottedname))
            super(Configuration, self).__setitem__(key, values)
            return values
        else:
            return value

    def __getattr__(self, key):
        return self[key]

def authtkt_factory(**kwargs):
    from kotti.security import list_groups_callback
    kwargs.setdefault('callback', list_groups_callback)
    return AuthTktAuthenticationPolicy(**kwargs)

def acl_factory(**kwargs):
    return ACLAuthorizationPolicy()

def cookie_session_factory(**kwargs):
    return UnencryptedCookieSessionFactoryConfig(**kwargs)

def none_factory(**kwargs):
    return None

# All of these can be set by passing them in the Paste Deploy settings:
configuration = Configuration(
    {
        'kotti.templates.master_view': 'kotti:templates/view/master.pt',
        'kotti.templates.master_edit': 'kotti:templates/edit/master.pt',
        'kotti.templates.base_css': 'kotti:static/base.css',
        'kotti.templates.view_css': 'kotti:static/view.css',
        'kotti.templates.edit_css': 'kotti:static/edit.css',
        'kotti.configurators': '',
        'kotti.includes': 'kotti.events kotti.views.view kotti.views.edit kotti.views.login kotti.views.manage',
        'kotti.available_types': 'kotti.resources.Document',
        'kotti.authn_policy_factory': 'kotti.authtkt_factory',
        'kotti.authz_policy_factory': 'kotti.acl_factory',
        'kotti.session_factory': 'kotti.cookie_session_factory',
        'kotti.principals': 'kotti.security.principals',
    },
    dotted_names=set([
        'kotti.configurators',
        'kotti.includes',
        'kotti.available_types',
        'kotti.authn_policy_factory',
        'kotti.authz_policy_factory',
        'kotti.session_factory',
        'kotti.principals',
        ]),
    )

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    for key in configuration:
        if key in settings:
            configuration[key] = settings.pop(key)

    # Allow extending packages to change 'configuration' w/ Python:
    for func in configuration['kotti.configurators']:
        func(configuration) # XXX testme

    secret1 = settings['kotti.secret']
    secret2 = settings.get('kotti.secret2', secret1)
    configuration.secret = secret1
    configuration.secret2 = secret2    

    from kotti.resources import appmaker
    engine = engine_from_config(settings, 'sqlalchemy.')
    get_root = appmaker(engine)

    authentication_policy = configuration[
        'kotti.authn_policy_factory'][0](secret=secret1)
    authorization_policy = configuration[
        'kotti.authz_policy_factory'][0]()
    session_factory = configuration['kotti.session_factory'][0](secret=secret2)

    config = Configurator(
        settings=settings,
        root_factory=get_root,
        authentication_policy=authentication_policy,
        authorization_policy=authorization_policy,
        session_factory=session_factory,
        )

    _configure_base_views(config)

    # Include modules listed in 'includeme' configuration:
    for module in configuration['kotti.includes']:
        config.include(module)

    return config.make_wsgi_app()

def _configure_base_views(config):
    from kotti.resources import Node

    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('static-kotti', 'kotti:static')
    config.add_view('kotti.views.view.view_node_default', context=Node)
    config.add_view(
        'kotti.views.edit.add_node',
        name='add',
        permission='add',
        renderer='templates/edit/add.pt',
        )
    config.add_view(
        'kotti.views.edit.move_node',
        name='move',
        permission='edit',
        renderer='templates/edit/move.pt',
        )

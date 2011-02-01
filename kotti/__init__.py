from sqlalchemy import engine_from_config
#from pyramid.authentication import AuthTktAuthenticationPolicy
#from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.util import DottedNameResolver

from kotti.resources import appmaker
from kotti.resources import Node

class Configuration(dict):
    """A dict that can resolve dotted names to Python objects the
    first time they're accessed.
    """
    dotted_names = set((
        'kotti.includes',
        'kotti.available_types',
        ))

    def __getitem__(self, key):
        value = super(Configuration, self).__getitem__(key)
        if key in self.dotted_names and isinstance(value, basestring):
            values = []
            for dottedname in value.split():
                try:
                    values.append(DottedNameResolver(None).resolve(dottedname))
                except ImportError: # pragma: no coverage
                    raise ValueError("Could not resolve %r." % dottedname)
            super(Configuration, self).__setitem__(key, values)
            return values
        else:
            return value

# All of these can be set by passing them in the Paste Deploy settings:
configuration = Configuration({
    'kotti.templates.snippets': 'kotti:templates/snippets.pt',
    'kotti.templates.master_view': 'kotti:templates/view/master.pt',
    'kotti.templates.master_edit': 'kotti:templates/edit/master.pt',
    'kotti.includes': 'kotti.views.view kotti.views.edit',
    'kotti.available_types': 'kotti.resources.Document',
    })

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    for key in configuration:
        if key in settings:
            configuration[key] = settings.pop(key)
    secret = settings.pop("kotti.secret")

    engine = engine_from_config(settings, 'sqlalchemy.')
    get_root = appmaker(engine)

    # XXX These two want to be configurable:
#    authentication_policy = AuthTktAuthenticationPolicy(secret)
#    authorization_policy = ACLAuthorizationPolicy()
    session_factory = UnencryptedCookieSessionFactoryConfig(secret)

    config = Configurator(
        settings=settings,
        root_factory=get_root,
#        authentication_policy=authentication_policy,
#        authorization_policy=authorization_policy,
        session_factory=session_factory,
        )

    _configure_base_views(config)

    # Include modules listed in 'includeme' configuration:
    for module in configuration['kotti.includes']:
        config.include(module)

    return config.make_wsgi_app()

def _configure_base_views(config):
    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('static-kotti', 'kotti:static')
    config.add_view('kotti.views.view.view_node_default', context=Node)
    config.add_view(
        'kotti.views.edit.add_node',
        name='add',
        permission='add',
        renderer='templates/edit/add.pt',
        )

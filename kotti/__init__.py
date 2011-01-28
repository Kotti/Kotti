from sqlalchemy import engine_from_config
from pyramid.config import Configurator
#from pyramid.authentication import AuthTktAuthenticationPolicy
#from pyramid.authorization import ACLAuthorizationPolicy

from kotti.resources import appmaker
from kotti.resources import Node

# All of these can be set by passing them in the Paste Deploy settings:
configuration = {
    'kotti.templates.snippets': 'kotti:templates/snippets.pt',
    'kotti.templates.master_view': 'kotti:templates/master_view.pt',
    'kotti.templates.master_edit': 'kotti:templates/master_edit.pt',
    'kotti.includes': 'kotti.views.view kotti.views.edit',
    }

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    for key in configuration:
        if key in settings:
            configuration[key] = settings.pop(key)

    engine = engine_from_config(settings, 'sqlalchemy.')
    get_root = appmaker(engine)

    # XXX These two want to be configurable:
#    authentication_policy = AuthTktAuthenticationPolicy(settings.pop('secret'))
#    authorization_policy = ACLAuthorizationPolicy()

    config = Configurator(
        settings=settings,
        root_factory=get_root,
#        authentication_policy=authentication_policy,
#        authorization_policy=authorization_policy,
        )

    config.add_static_view('static-deform', 'deform:static')
    config.add_static_view('static-kotti', 'kotti:static')
    config.add_view('kotti.views.node_default_view', context=Node)

    # Include modules listed in 'includeme' configuration:
    modules = [m.strip() for m in configuration['kotti.includes'].split()]
    for module in modules:
        config.include(module)

    return config.make_wsgi_app()

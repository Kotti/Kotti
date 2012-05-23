import pkg_resources
import warnings

from sqlalchemy import engine_from_config
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import BeforeRender
from pyramid.threadlocal import get_current_registry
from pyramid.util import DottedNameResolver
from pyramid_beaker import session_factory_from_settings

import kotti.patches
kotti.patches   # pyflakes

from kotti.sqla import Base as KottiBase
from kotti.util import request_cache

metadata = MetaData()
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base(cls=KottiBase)
Base.metadata = metadata
Base.query = DBSession.query_property()


def authtkt_factory(**settings):
    from kotti.security import list_groups_callback
    return AuthTktAuthenticationPolicy(
        secret=settings['kotti.secret2'], callback=list_groups_callback)

def acl_factory(**settings):
    return ACLAuthorizationPolicy()

def beaker_session_factory(**settings):
    return session_factory_from_settings(settings)

def none_factory(**kwargs):  # pragma: no cover
    return None

# All of these can be set by passing them in the Paste Deploy settings:
conf_defaults = {
    'kotti.templates.api': 'kotti.views.util.TemplateAPI',
    'kotti.configurators': '',
    'pyramid.includes': '',
    'kotti.includes': '',  # BBB
    'kotti.base_includes': 'kotti kotti.events kotti.views kotti.views.view kotti.views.edit kotti.views.login kotti.views.file kotti.views.image kotti.views.users kotti.views.site_setup kotti.views.slots',
    'kotti.asset_overrides': '',
    'kotti.use_tables': '',
    'kotti.root_factory': 'kotti.resources.default_get_root',
    'kotti.populators': 'kotti.populate.populate',
    'kotti.available_types': 'kotti.resources.Document kotti.resources.File kotti.resources.Image',
    'kotti.authn_policy_factory': 'kotti.authtkt_factory',
    'kotti.authz_policy_factory': 'kotti.acl_factory',
    'kotti.session_factory': 'kotti.beaker_session_factory',
    'kotti.principals_factory': 'kotti.security.principals_factory',
    'kotti.date_format': 'medium',
    'kotti.datetime_format': 'medium',
    'kotti.time_format': 'medium',
    'pyramid_deform.template_search_path': 'kotti:templates/deform',
    }

conf_dotted = set([
    'kotti.templates.api',
    'kotti.configurators',
    'kotti.base_includes',
    'kotti.root_factory',
    'kotti.populators',
    'kotti.available_types',
    'kotti.authn_policy_factory',
    'kotti.authz_policy_factory',
    'kotti.session_factory',
    'kotti.principals_factory',
    ])

def get_version():
    return pkg_resources.require("Kotti")[0].version

@request_cache(lambda: None)
def get_settings():
    from kotti.resources import Settings
    session = DBSession()
    db_settings = session.query(Settings).order_by(desc(Settings.id)).first()
    if db_settings is not None:
        reg_settings = dict(get_current_registry().settings)
        reg_settings.update(db_settings.data)
        return reg_settings
    else:
        return get_current_registry().settings

def _resolve_dotted(d, keys=conf_dotted):
    for key in keys:
        value = d[key]
        if not isinstance(value, basestring):
            continue
        new_value = []
        for dottedname in value.split():
            new_value.append(DottedNameResolver(None).resolve(dottedname))
        d[key] = new_value

def main(global_config, **settings):
    """ This function is a 'paste.app_factory' and returns a WSGI
    application.
    """
    config = base_configure(global_config, **settings)
    return config.make_wsgi_app()

def base_configure(global_config, **settings):
    """Resolve dotted names in settings, include plug-ins and create a
    Configurator.
    """
    from kotti.resources import appmaker

    for key, value in conf_defaults.items():
        settings.setdefault(key, value)

    for key, value in settings.items():
        if isinstance(settings[key], basestring):
            settings[key] = unicode(value, 'utf8')

    # Allow extending packages to change 'settings' w/ Python:
    _resolve_dotted(settings, keys=('kotti.configurators',))
    for func in settings['kotti.configurators']:
        func(settings)

    _resolve_dotted(settings)
    secret1 = settings['kotti.secret']
    settings.setdefault('kotti.secret2', secret1)

    # BBB: Merge ``kotti.includes`` into pyramid.includes.
    if settings['kotti.includes']:
        warnings.warn(
            "The 'kotti.includes' setting has been deprecated as of "
            "Kotti 0.6.1.  Use 'pyramid.includes' instead.",
            DeprecationWarning)
        settings.setdefault('pyramid.includes', '')
        settings['pyramid.includes'] += ' ' + settings['kotti.includes']

    # We'll process ``pyramid_includes`` later by hand, to allow
    # overrides of configuration from ``kotti.base_includes``:
    pyramid_includes = settings.pop('pyramid.includes', '')

    config = Configurator(settings=settings)
    config.begin()

    config.registry.settings['pyramid.includes'] = pyramid_includes

    # Include modules listed in 'kotti.base_includes':
    for module in settings['kotti.base_includes']:
        config.include(module)
    config.commit()

    # Modules in 'pyramid.includes' may override 'kotti.base_includes':
    if pyramid_includes:
        for module in pyramid_includes.split():
            config.include(module)
    config.commit()

    engine = engine_from_config(settings, 'sqlalchemy.')
    config._set_root_factory(appmaker(engine))

    return config

def includeme(config):
    import kotti.views.util

    settings = config.get_settings()

    authentication_policy = settings[
        'kotti.authn_policy_factory'][0](**settings)
    authorization_policy = settings[
        'kotti.authz_policy_factory'][0](**settings)
    session_factory = settings['kotti.session_factory'][0](**settings)
    if authentication_policy:
        config.set_authentication_policy(authentication_policy)
    if authorization_policy:
        config.set_authorization_policy(authorization_policy)
    config.set_session_factory(session_factory)

    config.add_subscriber(
        kotti.views.util.add_renderer_globals, BeforeRender)

    for override in [a.strip()
                     for a in settings['kotti.asset_overrides'].split()
                     if a.strip()]:
        config.override_asset(to_override='kotti', override_with=override)

    config.add_translation_dirs('kotti:locale')

    return config

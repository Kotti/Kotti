import pkg_resources

from sqlalchemy import engine_from_config
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
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

from kotti.sqla import Base as KottiBase


metadata = MetaData()
DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base(cls=KottiBase)
Base.metadata = metadata
Base.query = DBSession.query_property()
TRUE_VALUES = ('1', 'y', 'yes', 't', 'true')
FALSE_VALUES = ('0', 'n', 'no', 'f', 'false', 'none')


def authtkt_factory(**settings):
    from kotti.security import list_groups_callback
    kwargs = dict(
        secret=settings['kotti.secret2'],
        hashalg='sha512',
        callback=list_groups_callback,
        )
    try:
        return AuthTktAuthenticationPolicy(**kwargs)
    except TypeError:
        # BBB with Pyramid < 1.4
        kwargs.pop('hashalg')
        return AuthTktAuthenticationPolicy(**kwargs)


def acl_factory(**settings):
    return ACLAuthorizationPolicy()


def beaker_session_factory(**settings):
    return session_factory_from_settings(settings)


def none_factory(**kwargs):  # pragma: no cover
    return None

# All of these can be set by passing them in the Paste Deploy settings:
conf_defaults = {
    'kotti.alembic_dirs': 'kotti:alembic',
    'kotti.asset_overrides': '',
    'kotti.authn_policy_factory': 'kotti.authtkt_factory',
    'kotti.authz_policy_factory': 'kotti.acl_factory',
    'kotti.available_types': ' '.join([
        'kotti.resources.Document',
        'kotti.resources.File',
        'kotti.resources.Image',
        ]),
    'kotti.base_includes': ' '.join([
        'kotti',
        'kotti.filedepot',
        'kotti.events',
        'kotti.sanitizers',
        'kotti.views',
        'kotti.views.cache',
        'kotti.views.view',
        'kotti.views.edit',
        'kotti.views.edit.actions',
        'kotti.views.edit.content',
        'kotti.views.edit.default_views',
        'kotti.views.edit.upload',
        'kotti.views.file',
        'kotti.views.image',
        'kotti.views.login',
        'kotti.views.navigation',
        'kotti.views.users',
        ]),
    'kotti.caching_policy_chooser': (
        'kotti.views.cache.default_caching_policy_chooser'),
    'kotti.configurators': '',
    'kotti.date_format': 'medium',
    'kotti.datetime_format': 'medium',
    'kotti.depot.0.backend': 'kotti.filedepot.DBFileStorage',
    'kotti.depot.0.name': 'dbfiles',
    'kotti.fanstatic.edit_needed': 'kotti.fanstatic.edit_needed',
    'kotti.fanstatic.view_needed': 'kotti.fanstatic.view_needed',
    'kotti.max_file_size': '10',
    'kotti.modification_date_excludes': ' '.join([
        'kotti.resources.Node.position',
    ]),
    'kotti.populators': 'kotti.populate.populate',
    'kotti.principals_factory': 'kotti.security.principals_factory',
    'kotti.register': 'False',
    'kotti.register.group': '',
    'kotti.register.role': '',
    'kotti.request_factory': 'kotti.request.Request',
    'kotti.root_factory': 'kotti.resources.default_get_root',
    'kotti.sanitizers': ' '.join([
        'xss_protection:kotti.sanitizers.xss_protection',
        'minimal_html:kotti.sanitizers.minimal_html',
        'no_html:kotti.sanitizers.no_html',
        ]),
    'kotti.sanitize_on_write': ' '.join([
        'kotti.resources.Document.body:xss_protection',
        'kotti.resources.Content.title:no_html',
        'kotti.resources.Content.description:no_html',
        ]),
    'kotti.search_content': 'kotti.views.util.default_search_content',
    'kotti.session_factory': 'kotti.beaker_session_factory',
    'kotti.static.edit_needed': '',  # BBB
    'kotti.static.view_needed': '',  # BBB
    'kotti.templates.api': 'kotti.views.util.TemplateAPI',
    'kotti.time_format': 'medium',
    'kotti.url_normalizer': 'kotti.url_normalizer.url_normalizer',
    'kotti.url_normalizer.map_non_ascii_characters': True,
    'kotti.use_tables': '',
    'kotti.use_workflow': 'kotti:workflow.zcml',
    'kotti.zcml_includes': ' '.join([
        ]),
    'pyramid.includes': '',
    'pyramid_deform.template_search_path': 'kotti:templates/deform',
    }

conf_dotted = set([
    'kotti.authn_policy_factory',
    'kotti.authz_policy_factory',
    'kotti.available_types',
    'kotti.base_includes',
    'kotti.caching_policy_chooser',
    'kotti.configurators',
    'kotti.fanstatic.edit_needed',
    'kotti.fanstatic.view_needed',
    'kotti.modification_date_excludes',
    'kotti.populators',
    'kotti.principals_factory',
    'kotti.request_factory',
    'kotti.root_factory',
    'kotti.search_content',
    'kotti.session_factory',
    'kotti.templates.api',
    'kotti.url_normalizer',
    ])


def get_version():
    return pkg_resources.require("Kotti")[0].version


def get_settings():
    return get_current_registry().settings


def _resolve_dotted(d, keys=conf_dotted):

    resolved = d.copy()

    for key in keys:
        value = resolved[key]
        if not isinstance(value, basestring):
            continue
        new_value = []
        for dottedname in value.split():
            new_value.append(DottedNameResolver(None).resolve(dottedname))
        resolved[key] = new_value

    return resolved


def main(global_config, **settings):
    # This function is a 'paste.app_factory' and returns a WSGI
    # application.

    from kotti.resources import initialize_sql
    config = base_configure(global_config, **settings)
    engine = engine_from_config(config.registry.settings, 'sqlalchemy.')
    initialize_sql(engine)
    return config.make_wsgi_app()


def base_configure(global_config, **settings):
    # Resolve dotted names in settings, include plug-ins and create a
    # Configurator.

    from kotti.resources import get_root

    for key, value in conf_defaults.items():
        settings.setdefault(key, value)

    for key, value in settings.items():
        if key.startswith('kotti') and isinstance(value, basestring):
            settings[key] = unicode(value, 'utf8')

    # Allow extending packages to change 'settings' w/ Python:
    k = 'kotti.configurators'
    for func in _resolve_dotted(settings, keys=(k,))[k]:
        func(settings)

    settings = _resolve_dotted(settings)
    secret1 = settings['kotti.secret']
    settings.setdefault('kotti.secret2', secret1)

    # We'll process ``pyramid_includes`` later by hand, to allow
    # overrides of configuration from ``kotti.base_includes``:
    pyramid_includes = settings.pop('pyramid.includes', '')

    config = Configurator(
        request_factory=settings['kotti.request_factory'][0],
        settings=settings)
    config.begin()

    config.hook_zca()
    config.include('pyramid_zcml')

    # Chameleon bindings were removed from Pyramid core since pyramid>=1.5a2
    config.include('pyramid_chameleon')

    config.registry.settings['pyramid.includes'] = pyramid_includes

    # Include modules listed in 'kotti.base_includes':
    for module in settings['kotti.base_includes']:
        config.include(module)
    config.commit()

    # Modules in 'pyramid.includes' and 'kotti.zcml_includes' may
    # override 'kotti.base_includes':
    if pyramid_includes:
        for module in pyramid_includes.split():
            config.include(module)

    for name in settings['kotti.zcml_includes'].strip().split():
        config.load_zcml(name)

    config.commit()

    config._set_root_factory(get_root)

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

    workflow = settings['kotti.use_workflow']
    if workflow.lower() not in FALSE_VALUES:
        config.load_zcml(workflow)

    return config

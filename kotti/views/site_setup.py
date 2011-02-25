from kotti.util import ViewLink
from kotti.views.util import TemplateAPIEdit
from kotti.views.util import is_root

CONTROL_PANEL_LINKS = [
    ViewLink('setup-users', u'User Management'),
    ]

def main(context, request):
    api = TemplateAPIEdit(
        context, request,
        page_title=u"Site Setup - %s" % context.title,
        cp_links=CONTROL_PANEL_LINKS,
        )

    return {'api': api}

def users(context, request):
    api = TemplateAPIEdit(
        context, request,
        page_title=u"User Management - %s" % context.title,
        cp_links=CONTROL_PANEL_LINKS,
        )

    return {
        'api': api,
        }

def includeme(config):
    config.add_view(
        main,
        name='setup',
        permission='admin',
        custom_predicates=(is_root,),
        renderer='../templates/site-setup/main.pt',
        )

    config.add_view(
        users,
        name='setup-users',
        permission='admin',
        custom_predicates=(is_root,),
        renderer='../templates/site-setup/users.pt',
        )

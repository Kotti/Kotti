from kotti.util import _
from kotti.util import ViewLink
from kotti.views.util import template_api
from kotti.views.util import is_root


CONTROL_PANEL_LINKS = [
    ViewLink('setup-users', title=_(u'User Management')),
    ]

def main(context, request):
    api = template_api(
        context, request,
        cp_links=CONTROL_PANEL_LINKS,
        )
    api.page_title = _(u"Site Setup - ${title}",
                       mapping=dict(title=api.site_title))
    return {'api': api}

def includeme(config):
    config.add_view(
        main,
        name='setup',
        permission='admin',
        custom_predicates=(is_root,),
        renderer='kotti:templates/site-setup/main.pt',
        )

from kotti.security import ROLES
from kotti.security import map_principals_with_local_roles
from kotti.views.util import TemplateAPIEdit

def share_node(context, request):
    return {
        'api': TemplateAPIEdit(context, request),
        'form': u'foo',
        'all_roles': ROLES,
        'principals_to_roles': map_principals_with_local_roles(context),
        }

def includeme(config):
    config.add_view(
        share_node,
        name='share',
        permission='manage',
        renderer='templates/edit/share.pt',
        )

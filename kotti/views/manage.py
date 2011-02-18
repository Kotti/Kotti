from pyramid.location import lineage

from kotti.security import ROLES
from kotti.security import roles_to_principals
from kotti.views.util import TemplateAPIEdit

def share_node(context, request):
    local_roles_to_principals = roles_to_principals(context)
    local_roles = []

    for role_id, principals in local_roles_to_principals.items():
        local_roles.append((ROLES[role_id], principals))

    inherited_roles_to_principals = {}
    inherited_roles = []
    for item in list(lineage(context))[1:]:
        inherited_roles_to_principals = roles_to_principals(
            item, inherited_roles_to_principals)

    for role_id, principals in inherited_roles_to_principals.items():
        principals = [p for p in principals
                      if p not in local_roles_to_principals.get(role_id, [])]
        if principals:
            inherited_roles.append((ROLES[role_id], principals))

    return {
        'api': TemplateAPIEdit(context, request),
        'form': u'foo',
        'all_roles': ROLES,
        'local_roles': local_roles,
        'inherited_roles': inherited_roles,
        }

def includeme(config):
    config.add_view(
        share_node,
        name='share',
        permission='manage',
        renderer='templates/edit/share.pt',
        )

from kotti.security import ROLES
from kotti.security import all_groups_raw
from kotti.security import get_principals
from kotti.views.util import TemplateAPIEdit

def _roles_to_principals(context, roles_to_principals=None):
    groups = all_groups_raw(context)
    if groups is None:
        return {}

    principals = get_principals()
    if roles_to_principals is None:
        roles_to_principals = {}

    for principal_id, groups in groups.items():
        try:
            principal = principals[principal_id]
        except KeyError:
            # We couldn't find that principal in the user
            # database, so we'll ignore it:
            continue
        for group_id in groups:
            if group_id not in roles_to_principals:
                roles_to_principals[group_id] = []
            principals = roles_to_principals[group_id]
            if principal not in principals:
                principals.append(principal)

    return roles_to_principals

def share_node(context, request):
    local_roles_to_principals = _roles_to_principals(context)
    local_roles = []
    for role_id, principals in local_roles_to_principals.items():
        local_roles.append((ROLES[role_id], principals))

    return {
        'api': TemplateAPIEdit(context, request),
        'form': u'foo',
        'all_roles': ROLES,
        'local_roles': local_roles,
        }

def includeme(config):
    config.add_view(
        share_node,
        name='share',
        permission='manage',
        renderer='templates/edit/share.pt',
        )

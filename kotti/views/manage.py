from kotti.security import ROLES
from kotti.security import all_groups_raw
from kotti.security import get_principals
from kotti.views.util import TemplateAPIEdit

def share_node(context, request):
    principals = get_principals()
    groups = all_groups_raw(context)
    roles_to_principals = {}
    if groups is not None:
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
                roles_to_principals[group_id].append(principal)

    local_groups = []
    for role_id, principals in roles_to_principals.items():
        local_groups.append((ROLES[role_id], principals))

    return {
        'api': TemplateAPIEdit(context, request),
        'form': u'foo',
        'roles': ROLES,
        'local_groups': local_groups,
        }

def includeme(config):
    config.add_view(
        share_node,
        name='share',
        permission='manage',
        renderer='templates/edit/share.pt',
        )

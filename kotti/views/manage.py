from pyramid.httpexceptions import HTTPFound

from kotti.security import get_principals
from kotti.security import ROLES
from kotti.security import map_principals_with_local_roles
from kotti.security import set_groups
from kotti.security import list_groups_raw
from kotti.security import list_groups_ext
from kotti.views.util import TemplateAPIEdit

def share_node(context, request):
    flash = request.session.flash
    principals = get_principals()
    all_roles = sorted(ROLES.values(), key=lambda r:r.id)

    if 'apply' in request.params:
        changed = False
        p_to_r = {}
        for name in request.params:
            if name.startswith('orig-role::'):
                token, principal_id, role_id = name.split('::')
                new_value = bool(request.params.get(
                    'role::%s::%s' % (principal_id, role_id)))
                if principal_id not in p_to_r:
                    p_to_r[principal_id] = set()
                if new_value:
                    p_to_r[principal_id].add(role_id)

        for principal_id, role_ids in p_to_r.items():
            orig_group_ids = set(r for r in list_groups_raw(principal_id, context))
            orig_role_ids = [r for r in orig_group_ids if r.startswith('role:')]
            orig_role_ids = set(orig_role_ids)
            if role_ids != orig_role_ids:
                changed = True
                new_group_ids = orig_group_ids - orig_role_ids | role_ids
                set_groups(principal_id, context, new_group_ids)

        if changed:
            flash(u'Your changes have been applied.', 'success')
        else:
            flash(u'No changes made.', 'info')
        return HTTPFound(location=request.url)

    existing = map_principals_with_local_roles(context)
    def with_roles(entry):
        all_groups = entry[1][0]
        return [g for g in all_groups if g.startswith('role:')]
    existing = filter(with_roles, existing)
    seen = set([entry[0].id for entry in existing])

    entries = []

    if 'search' in request.params:
        query = request.params['query']
        found = False
        for p in principals.search(query):
            found = True
            if p.id not in seen:
                entries.append((p, list_groups_ext(p.id, context)))
        if not found:
            flash(u'No users or groups found.', 'error')

    entries = existing + entries

    return {
        'api': TemplateAPIEdit(context, request),
        'entries': entries,
        'all_roles': all_roles,
        'principals_to_roles': map_principals_with_local_roles(context),
        }

def includeme(config):
    config.add_view(
        share_node,
        name='share',
        permission='manage',
        renderer='../templates/edit/share.pt',
        )

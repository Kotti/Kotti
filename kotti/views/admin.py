from pyramid.exceptions import Forbidden
from pyramid.httpexceptions import HTTPFound

from kotti.security import get_principals
from kotti.security import map_principals_with_local_roles
from kotti.security import set_groups
from kotti.security import list_groups_raw
from kotti.security import list_groups_ext
from kotti.security import ROLES
from kotti.security import SHARING_ROLES
from kotti.util import Link
from kotti.views.util import TemplateAPIEdit
from kotti.views.util import is_root

CONTROL_PANEL_LINKS = [
    Link('cp-users', u'User Management'),
    ]

def share_node(context, request):
    flash = request.session.flash
    principals = get_principals()
    available_roles = [ROLES[role_name] for role_name in SHARING_ROLES]

    if 'apply' in request.params:
        changed = False
        p_to_r = {}
        for name in request.params:
            if name.startswith('orig-role::'):
                token, principal_name, role_name = name.split('::')
                if role_name not in SHARING_ROLES:
                    raise Forbidden()
                new_value = bool(request.params.get(
                    'role::%s::%s' % (principal_name, role_name)))
                if principal_name not in p_to_r:
                    p_to_r[principal_name] = set()
                if new_value:
                    p_to_r[principal_name].add(role_name)

        for principal_name, new_role_names in p_to_r.items():
            # We have to be careful with roles that aren't mutable here:
            orig_role_names = set(list_groups_raw(principal_name, context))
            orig_sharing_role_names = set(
                r for r in orig_role_names if r in SHARING_ROLES)
            if new_role_names != orig_sharing_role_names:
                changed = True
                final_role_names = orig_role_names - set(SHARING_ROLES)
                final_role_names |= new_role_names
                set_groups(principal_name, context, final_role_names)

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
    seen = set([entry[0].name for entry in existing])

    entries = []

    if 'search' in request.params:
        query = request.params['query']
        found = False
        for p in principals.search(query):
            found = True
            if p.name not in seen:
                entries.append((p, list_groups_ext(p.name, context)))
        if not found:
            flash(u'No users or groups found.', 'info')

    entries = existing + entries

    return {
        'api': TemplateAPIEdit(context, request),
        'entries': entries,
        'available_roles': available_roles,
        'principals_to_roles': map_principals_with_local_roles(context),
        }

def control_panel_main(context, request):
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
        share_node,
        name='share',
        permission='manage',
        renderer='../templates/edit/share.pt',
        )

    config.add_view(
        control_panel_main,
        name='cp',
        permission='admin',
        custom_predicates=(is_root,),
        renderer='../templates/control-panel/main.pt',
        )

    config.add_view(
        users,
        name='cp-users',
        permission='admin',
        custom_predicates=(is_root,),
        renderer='../templates/control-panel/users.pt',
        )

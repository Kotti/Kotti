from kotti.security import get_principals
from kotti.security import ROLES
from kotti.security import map_principals_with_local_roles
from kotti.security import list_groups_ext
from kotti.views.util import TemplateAPIEdit

def share_node(context, request):
    entries = []

    existing = map_principals_with_local_roles(context)
    def with_roles(entry):
        all_groups = entry[1][0]
        return [g for g in all_groups if g.startswith('role:')]
    existing = filter(with_roles, existing)
    seen = set([entry[0].id for entry in existing])

    principals = get_principals()
    query = request.params.get('query')
    if query is not None:
        for p in principals.search(query):
            if p.id not in seen:
                entries.append((p, list_groups_ext(p.id, context)))

    entries = existing + entries
    
    return {
        'api': TemplateAPIEdit(context, request),
        'entries': entries,
        'all_roles': ROLES,
        'principals_to_roles': map_principals_with_local_roles(context),
        }

def includeme(config):
    config.add_view(
        share_node,
        name='share',
        permission='manage',
        renderer='../templates/edit/share.pt',
        )

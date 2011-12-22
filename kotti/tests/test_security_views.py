import colander

from kotti.testing import DummyRequest
from kotti.testing import UnitTestBase

class TestUserManagement(UnitTestBase):
    def test_roles(self):
        from kotti.resources import get_root
        from kotti.security import USER_MANAGEMENT_ROLES
        from kotti.views.users import users_manage

        root = get_root()
        request = DummyRequest()
        self.assertEqual(
            [r.name for r in users_manage(root, request)['available_roles']],
            USER_MANAGEMENT_ROLES)

    def test_search(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.tests.test_node_views import TestNodeShare
        from kotti.views.users import users_manage

        root = get_root()
        request = DummyRequest()
        P = get_principals()
        TestNodeShare.add_some_principals()

        request.params['search'] = u''
        request.params['query'] = u'Joe'
        entries = users_manage(root, request)['entries']
        self.assertEqual(len(entries), 0)
        self.assertEqual(request.session.pop_flash('notice'),
                         [u'No users or groups found.'])
        request.params['query'] = u'Bob'
        entries = users_manage(root, request)['entries']
        self.assertEqual(entries[0][0], P['bob'])
        self.assertEqual(entries[0][1], ([], []))
        self.assertEqual(entries[1][0], P['group:bobsgroup'])
        self.assertEqual(entries[1][1], ([], []))

        P[u'bob'].groups = [u'group:bobsgroup']
        P[u'group:bobsgroup'].groups = [u'role:admin']
        entries = users_manage(root, request)['entries']
        self.assertEqual(entries[0][1],
                         (['group:bobsgroup', 'role:admin'], ['role:admin']))
        self.assertEqual(entries[1][1], (['role:admin'], []))

    def test_apply(self):
        from kotti.resources import get_root
        from kotti.security import get_principals
        from kotti.security import list_groups
        from kotti.tests.test_node_views import TestNodeShare
        from kotti.views.users import users_manage

        root = get_root()
        request = DummyRequest()

        TestNodeShare.add_some_principals()
        bob = get_principals()[u'bob']

        request.params['apply'] = u''
        users_manage(root, request)
        self.assertEqual(request.session.pop_flash('notice'),
                         [u'No changes made.'])
        self.assertEqual(list_groups('bob'), [])
        bob.groups = [u'role:special']

        request.params['role::bob::role:owner'] = u'1'
        request.params['role::bob::role:editor'] = u'1'
        request.params['orig-role::bob::role:owner'] = u''
        request.params['orig-role::bob::role:editor'] = u''

        users_manage(root, request)
        self.assertEqual(request.session.pop_flash('success'),
                         [u'Your changes have been saved.'])
        self.assertEqual(
            set(list_groups('bob')),
            set(['role:owner', 'role:editor', 'role:special'])
            )

    def test_group_validator(self):
        from kotti.views.users import group_validator
        self.assertRaises(
            colander.Invalid,
            group_validator, None, u'this-group-never-exists')

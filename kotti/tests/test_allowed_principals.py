from kotti.testing import DummyRequest
from kotti.testing import EventTestBase
from kotti.testing import UnitTestBase


class TestAllowedPrincipals(EventTestBase, UnitTestBase):
    def test_empty(self):
        from kotti.resources import get_root
        assert get_root().allowed_principals == []

    def test_allowed_principals(self):
        from kotti.resources import AllowedPrincipal
        principal = AllowedPrincipal(name=u"role:owner")
        assert str(principal) == "<AllowedPrincipal ('role:owner')>"

    def test_add(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import AllowedPrincipal
        from kotti.resources import AllowedPrincipalsToContents

        root = get_root()
        root.allowed_principals = [u'role:viewer', u'role:owner']
        result = DBSession.query(AllowedPrincipal).filter(
            AllowedPrincipalsToContents.item == root).all()
        assert result[0].items == [root]
        assert root.allowed_principals == [u'role:viewer', u'role:owner']
        assert len(DBSession.query(AllowedPrincipal).all()) == 2

    def test_edit(self):
        from kotti.resources import get_root
        root = get_root()
        root.allowed_principals = [u'role:viewer', u'role:owner']
        assert root._allowed_principals[0].principal.name == u'role:viewer'
        root.allowed_principals = [u'system.Everyone', u'role:owner']
        assert root._allowed_principals[0].principal.name == u'system.Everyone'

    def test_association_proxy(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import AllowedPrincipal
        from kotti.resources import AllowedPrincipalsToContents
        from kotti.resources import Content

        root = get_root()
        c1 = root[u'content_1'] = Content()
        c1.allowed_principals = [u'role:viewer', u'role:owner']
        assert c1.allowed_principals == [u'role:viewer', u'role:owner']
        assert type(c1._allowed_principals[0]) == AllowedPrincipalsToContents
        assert type(c1._allowed_principals[0].principal) == AllowedPrincipal
        assert c1._allowed_principals[0].principal.name == u'role:viewer'
        assert c1._allowed_principals[1].principal.name == u'role:owner'
        assert len(c1._allowed_principals) == 2

        root[u'content_2'] = Content()
        c2 = root[u'content_2']
        c2.allowed_principals = [u'role:owner', u'bob']
        assert len(c2._allowed_principals) == 2
        assert c2._allowed_principals[0].principal.name == u'role:owner'
        assert c2._allowed_principals[1].principal.name == u'bob'
        assert len(DBSession.query(AllowedPrincipal).all()) == 3

    def test_delete_content_deletes_orphaned_allowed_principals(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import AllowedPrincipal, Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_2'] = Content()
        root[u'content_1'].allowed_principals = [u'role:viewer', u'role:owner']
        root[u'content_2'].allowed_principals = [u'role:owner']
        assert DBSession.query(AllowedPrincipal).count() == 2
        del root[u'content_1']
        assert DBSession.query(AllowedPrincipal).one().name == u'role:owner'

    def test_delete_principal_assignment_doesnt_touch_content(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import AllowedPrincipal
        from kotti.resources import AllowedPrincipalsToContents
        from kotti.resources import Content

        root = get_root()
        root[u'content_1'] = Content()
        root[u'content_1'].allowed_principals = [u'bob']

        ses = DBSession
        assert ses.query(AllowedPrincipal).count() == 1
        assert ses.query(Content).filter_by(name=u'content_1').count() == 1
        ses.delete(ses.query(AllowedPrincipalsToContents).one())
        assert ses.query(Content).filter_by(name=u'content_1').count() == 1

    def test_delete_content_delete_principals_and_assignments(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import AllowedPrincipal
        from kotti.resources import AllowedPrincipalsToContents
        from kotti.resources import Content
        from kotti.views.edit import delete_node

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'folder_1'].allowed_principals = [u'bob']
        root[u'folder_1'][u'content_1'] = Content()
        root[u'folder_1'][u'content_1'].allowed_principals = [u'role:owner']
        root[u'folder_1'][u'content_2'] = Content()
        root[u'folder_1'][u'content_2'].allowed_principals = [u'role:viewer']
        assert ses.query(AllowedPrincipal).count() == 3
        assert ses.query(AllowedPrincipalsToContents).count() == 3

        request = DummyRequest()
        request.POST['delete'] = 'on'
        delete_node(root[u'folder_1'], request)
        assert ses.query(AllowedPrincipal).count() == 0
        assert ses.query(AllowedPrincipalsToContents).count() == 0

    def test_get_content_items_from_principal(self):
        from kotti import DBSession
        from kotti.resources import get_root
        from kotti.resources import AllowedPrincipal, Content

        ses = DBSession
        root = get_root()
        root[u'folder_1'] = Content()
        root[u'folder_1'].allowed_principals = [u'bob', u'role:owner']
        root[u'folder_1'][u'content_1'] = Content()
        root[u'folder_1'][u'content_1'].allowed_principals = [u'role:viewer']
        root[u'folder_1'][u'content_2'] = Content()
        root[u'folder_1'][u'content_2'].allowed_principals = [
            u'bob', u'role:viewer']
        ap1 = ses.query(AllowedPrincipal).filter(
            AllowedPrincipal.name == u'bob').one()
        assert [rel.name for rel in ap1.items] == [u'folder_1', u'content_2']
        ap2 = ses.query(AllowedPrincipal).filter(
            AllowedPrincipal.name == u'role:owner').one()
        assert [rel.name for rel in ap2.items] == [u'folder_1']
        ap3 = ses.query(AllowedPrincipal).filter(
            AllowedPrincipal.name == u'role:viewer').one()
        assert [rel.name for rel in ap3.items] == [u'content_1', u'content_2']

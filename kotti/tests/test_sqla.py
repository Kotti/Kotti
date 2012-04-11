from unittest import TestCase

from pyramid.security import ALL_PERMISSIONS

class TestJsonType(TestCase):
    def make(self):
        from kotti.sqla import JsonType
        return JsonType()

    def test_process_bind_param_no_value(self):
        value = self.make().process_bind_param(None, None)
        assert value == None

    def test_process_bind_param_with_value(self):
        value = self.make().process_bind_param([{'foo': 'bar'}], None)
        assert value == '[{"foo": "bar"}]'

    def test_process_bind_param_with_mutationlist(self):
        from kotti.sqla import MutationList
        
        value = self.make().process_bind_param(
            MutationList([{'foo': 'bar'}]), None)

        assert value == '[{"foo": "bar"}]'

    def test_process_result_value_no_value(self):
        value = self.make().process_result_value(None, None)
        assert value == None

    def test_process_result_value_with_value(self):
        value = self.make().process_result_value('[{"foo": "bar"}]', None)
        assert value == [{"foo": "bar"}]

class TestACLType(TestCase):
    def make(self):
        from kotti.sqla import ACLType
        return ACLType()

    def test_process_bind_param_no_value(self):
        value = self.make().process_bind_param(None, None)
        assert value == None

    def test_process_bind_param_with_value(self):
        value = self.make().process_bind_param(
            [('Allow', 'role:admin', 'edit')], None)
        assert value == '[["Allow", "role:admin", "edit"]]'

    def test_process_bind_param_with_default_permissions(self):
        acl = [('Allow', 'role:admin', ALL_PERMISSIONS)]
        value = self.make().process_bind_param(acl, None)
        assert value == '[]'

    def test_process_bind_param_with_empty_list(self):
        value = self.make().process_bind_param([], None)
        assert value == '[]'

    def test_process_bind_param_with_default_permissions_and_others(self):
        acl = [
            ('Allow', 'role:admin', ALL_PERMISSIONS),
            ('Deny', 'role:admin', 'edit'),
            ]
        value = self.make().process_bind_param(acl, None)
        assert value == '[["Deny", "role:admin", "edit"]]'
        assert self.make().process_result_value(value, None) == acl

    def test_process_result_value_no_value(self):
        value = self.make().process_result_value(None, None)
        assert value == None

    def test_process_result_value_with_value(self):
        acl = self.make().process_result_value(
            '[["Allow", "role:admin", "edit"]]', None)
        assert acl == [
            ('Allow', 'role:admin', ALL_PERMISSIONS),
            ('Allow', 'role:admin', 'edit'),
            ]

class TestMutationList(TestCase):
    def test_radd(self):
        from kotti.sqla import MutationList
        mlist = MutationList(['foo'])
        assert ['bar'] + mlist == ['bar', 'foo']

class TestNestedMutationDict(TestCase):
    def test_setdefault_dict(self):
        from kotti.sqla import NestedMutationDict
        mdict = NestedMutationDict({})
        assert isinstance(mdict.setdefault('bar', {}), NestedMutationDict)

    def test_setdefault_list(self):
        from kotti.sqla import NestedMutationDict
        from kotti.sqla import NestedMutationList
        mdict = NestedMutationDict({})
        assert isinstance(mdict.setdefault('bar', []), NestedMutationList)

    def test_setdefault_parent(self):
        from kotti.sqla import NestedMutationDict
        mdict = NestedMutationDict({})
        assert mdict.setdefault('bar', []).__parent__ is mdict

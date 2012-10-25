from mock import MagicMock
from pyramid.security import ALL_PERMISSIONS


class TestNestedMutationDict:
    def test_dictwrapper_basics(self):
        from kotti.sqla import NestedMutationDict

        data = {}
        wrapper = NestedMutationDict(data)
        changed = wrapper.changed = MagicMock()

        wrapper['name'] = 'andy'
        assert data == {'name': 'andy'}
        assert wrapper == {'name': 'andy'}
        assert wrapper['name'] == 'andy'
        assert changed.call_count == 1

        wrapper['age'] = 77
        assert data == {'name': 'andy', 'age': 77}
        assert wrapper['age'] == 77
        assert wrapper['name'] == 'andy'
        assert changed.call_count == 2

        wrapper['age'] += 1
        assert data == {'name': 'andy', 'age': 78}
        assert wrapper['age'] == 78
        assert changed.call_count == 3

    def test_listwrapper_basics(self):
        from kotti.sqla import NestedMutationList

        data = []
        wrapper = NestedMutationList(data)
        changed = wrapper.changed = MagicMock()

        wrapper.append(5)
        assert data == [5]
        assert wrapper == [5]
        assert wrapper[0] == 5
        assert changed.call_count == 1

        wrapper.insert(0, 33)
        assert data == [33, 5]
        assert wrapper[0] == 33
        assert changed.call_count == 2

        del wrapper[0]
        assert data == [5]
        assert wrapper[0] == 5
        assert changed.call_count == 3

    def test_dictwrapper_wraps(self):
        from kotti.sqla import NestedMutationDict
        from kotti.sqla import NestedMutationList

        wrapper = NestedMutationDict(
            {'name': 'andy', 'age': 77, 'children': []})
        changed = wrapper.changed = MagicMock()

        wrapper['name'] = 'randy'
        assert changed.call_count == 1

        assert isinstance(wrapper['children'], NestedMutationList)
        wrapper['children'].append({'name': 'sandy', 'age': 33})
        assert changed.call_count == 2
        assert len(wrapper['children']), 1
        assert isinstance(wrapper['children'][0], NestedMutationDict)

    def test_listwrapper_wraps(self):
        from kotti.sqla import NestedMutationDict
        from kotti.sqla import NestedMutationList

        wrapper = NestedMutationList(
            [{'name': 'andy', 'age': 77, 'children': []}])
        changed = wrapper.changed = MagicMock()

        assert isinstance(wrapper[0], NestedMutationDict)
        assert isinstance(wrapper[0]['children'], NestedMutationList)
        assert changed.call_count == 0

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


class TestJsonType:
    def make(self):
        from kotti.sqla import JsonType
        return JsonType()

    def test_process_bind_param_no_value(self):
        value = self.make().process_bind_param(None, None)
        assert value is None

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
        assert value is None

    def test_process_result_value_with_value(self):
        value = self.make().process_result_value('[{"foo": "bar"}]', None)
        assert value == [{"foo": "bar"}]


class TestACLType:
    def make(self):
        from kotti.sqla import ACLType
        return ACLType()

    def test_process_bind_param_no_value(self):
        value = self.make().process_bind_param(None, None)
        assert value is None

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
        assert value is None

    def test_process_result_value_with_value(self):
        acl = self.make().process_result_value(
            '[["Allow", "role:admin", "edit"]]', None)
        assert acl == [
            ('Allow', 'role:admin', ALL_PERMISSIONS),
            ('Allow', 'role:admin', 'edit'),
            ]


class TestMutationList:
    def test_radd(self):
        from kotti.sqla import MutationList
        mlist = MutationList(['foo'])
        assert ['bar'] + mlist == ['bar', 'foo']

class TestMassageGroups:

    def test_massage_groups_in(self):
        from kotti.views.users import _massage_groups_in

        appstruct = {'groups': ['user-group', ],
                     'roles': ['role:editor', ]}
        _massage_groups_in(appstruct)
        assert appstruct['groups'] == ['role:editor', 'group:user-group']
        assert 'roles' not in appstruct

        appstruct = {}
        _massage_groups_in(appstruct)
        assert appstruct['groups'] == []
        assert 'roles' not in appstruct

    def test_massage_groups_out(self):
        from kotti.views.users import _massage_groups_out

        appstruct = {'groups': ['group:user-group', 'role:editor']}
        _massage_groups_out(appstruct)
        assert appstruct['groups'] == ['user-group']
        assert appstruct['roles'] == ['role:editor']

        appstruct = {'groups': []}
        _massage_groups_out(appstruct)
        assert appstruct['groups'] == []
        assert appstruct['roles'] == []

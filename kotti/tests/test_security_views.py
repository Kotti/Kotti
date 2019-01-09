import colander
import pytest
from mock import Mock
from mock import patch
from pytest import raises

from kotti.testing import DummyRequest


class TestUserManagement:
    def test_roles(self, root):
        from kotti.security import USER_MANAGEMENT_ROLES
        from kotti.views.users import UsersManage

        request = DummyRequest()
        assert [
            r.name for r in UsersManage(root, request)()["available_roles"]
        ] == USER_MANAGEMENT_ROLES

    def test_search(self, extra_principals, root):
        from kotti.security import get_principals
        from kotti.views.users import UsersManage

        request = DummyRequest()
        P = get_principals()

        request.params["search"] = ""
        request.params["query"] = "Joe"
        entries = UsersManage(root, request)()["entries"]
        assert len(entries) == 0
        assert request.session.pop_flash("info") == ["No users or groups were found."]
        request.params["query"] = "Bob"
        entries = UsersManage(root, request)()["entries"]
        assert entries[0][0] == P["bob"]
        assert entries[0][1] == ([], [])
        assert entries[1][0] == P["group:bobsgroup"]
        assert entries[1][1] == ([], [])

        P["bob"].groups = ["group:bobsgroup"]
        P["group:bobsgroup"].groups = ["role:admin"]
        entries = UsersManage(root, request)()["entries"]
        # assert entries[0][1] == (['group:bobsgroup', 'role:admin'], ['role:admin'])  # noqa
        assert set(entries[0][1][0]) == {"group:bobsgroup", "role:admin"}
        assert entries[0][1][1] == ["role:admin"]
        assert entries[1][1] == (["role:admin"], [])

    def test_apply(self, extra_principals, root):
        from kotti.security import get_principals
        from kotti.security import list_groups
        from kotti.views.users import UsersManage

        request = DummyRequest()

        bob = get_principals()["bob"]

        request.params["apply"] = ""
        UsersManage(root, request)()
        assert request.session.pop_flash("info") == ["No changes were made."]
        assert list_groups("bob") == []
        bob.groups = ["role:special"]

        request.params["role::bob::role:owner"] = "1"
        request.params["role::bob::role:editor"] = "1"
        request.params["orig-role::bob::role:owner"] = ""
        request.params["orig-role::bob::role:editor"] = ""

        UsersManage(root, request)()
        assert request.session.pop_flash("success") == ["Your changes have been saved."]
        assert set(list_groups("bob")) == {"role:owner", "role:editor", "role:special"}

    def test_group_validator(self, db_session):
        from kotti.views.users import group_validator

        with raises(colander.Invalid):
            group_validator(None, "this-group-never-exists")


class TestUserDelete:
    def test_user_delete(self, events, extra_principals, root):
        from kotti.security import get_principals
        from kotti.views.users import user_delete

        request = DummyRequest()
        bob = get_principals()["bob"]

        request.params["name"] = ""
        user_delete(root, request)
        assert request.session.pop_flash("error") == ["No name was given."]
        assert "bob" in get_principals().keys()

        request.params["name"] = "bob"
        result = user_delete(root, request)
        assert "api" in result
        api = result["api"]
        assert api.principal == bob
        assert api.principal_type == "User"
        assert "bob" in get_principals().keys()

        request.params["name"] = "john"
        request.params["delete"] = "delete"
        user_delete(root, request)
        assert request.session.pop_flash("error") == ["User was not found."]
        assert "bob" in get_principals().keys()

        request.params["name"] = "bob"
        request.params["delete"] = "delete"
        user_delete(root, request)
        with pytest.raises(KeyError):
            # noinspection PyStatementEffect
            get_principals()["bob"]

    def test_deleted_group_removed_in_usergroups(
        self, events, extra_principals, root, db_session
    ):
        from kotti.security import get_principals
        from kotti.views.users import user_delete

        request = DummyRequest()
        bob = get_principals()["bob"]
        bob.groups = ["group:bobsgroup"]
        assert bob.groups == ["group:bobsgroup"]

        request.params["name"] = "group:bobsgroup"
        request.params["delete"] = "delete"
        user_delete(root, request)
        db_session.expire(bob)
        with pytest.raises(KeyError):
            # noinspection PyStatementEffect
            get_principals()["group:bobsgroup"]
        assert bob.groups == []

    def test_deleted_group_removed_from_localgroups(
        self, events, extra_principals, root
    ):
        from kotti.security import set_groups
        from kotti.resources import LocalGroup
        from kotti.views.users import user_delete

        request = DummyRequest()
        set_groups("group:bobsgroup", root, ["role:admin"])
        local_group = LocalGroup.query.first()
        assert local_group.principal_name == "group:bobsgroup"
        assert local_group.node == root

        request.params["name"] = "group:bobsgroup"
        request.params["delete"] = "delete"
        user_delete(root, request)
        assert LocalGroup.query.first() is None

    def test_reset_owner_to_none(self, events, extra_principals, root):
        from kotti.resources import Content
        from kotti.views.users import user_delete

        request = DummyRequest()

        root["content_1"] = Content()
        root["content_1"].owner = "bob"
        assert root["content_1"].owner == "bob"

        request.params["name"] = "bob"
        request.params["delete"] = "delete"
        user_delete(root, request)
        assert root["content_1"].owner is None


# noinspection PyAttributeOutsideInit
class TestSetPassword:
    def setup_method(self, method):
        Form_patcher = patch("kotti.views.login.Form")
        self.Form_mock = Form_patcher.start()

        _find_user_patcher = patch("kotti.views.login._find_user")
        self._find_user_mock = _find_user_patcher.start()
        self.user = self._find_user_mock.return_value

        validate_token_patcher = patch("kotti.views.login.validate_token")
        self.validate_token_mock = validate_token_patcher.start()

        self.patchers = (Form_patcher, _find_user_patcher, validate_token_patcher)

    def teardown_method(self, method):
        for patcher in self.patchers:
            patcher.stop()

    def form_values(self, values):
        self.Form_mock.return_value.validate.return_value = values

    def test_success(self, root):
        from kotti.security import get_principals
        from kotti.views.login import set_password

        self.form_values(
            {
                "token": "mytoken",
                "email": "myemail",
                "password": "mypassword",
                "continue_to": "",
            }
        )
        self.user.confirm_token = "mytoken"
        self.user.password = "old_password"
        context, request = root, DummyRequest(post={"submit": "submit"})
        self.user.last_login_date = None
        res = set_password(context, request)

        assert self.user.confirm_token is None
        assert self.user.last_login_date is not None
        assert get_principals().validate_password("mypassword", self.user.password)
        assert res.status == "302 Found"

    def test_wrong_token(self, root):
        from kotti.security import get_principals
        from kotti.views.login import set_password

        self.form_values(
            {
                "token": "wrongtoken",
                "email": "myemail",
                "password": "mypassword",
                "continue_to": "",
            }
        )
        self.user.confirm_token = "mytoken"
        self.user.password = "old_password"
        context, request = root, DummyRequest(post={"submit": "submit"})
        res = set_password(context, request)

        assert self.user.confirm_token == "mytoken"
        assert not get_principals().validate_password("mypassword", self.user.password)
        assert not request.is_response(res)

    def test_inactive_user(self, root):
        from kotti.security import get_principals
        from kotti.views.login import set_password

        self.form_values(
            {
                "token": "mytoken",
                "email": "myemail",
                "password": "mypassword",
                "continue_to": "",
            }
        )
        self.user.confirm_token = "mytoken"
        self.user.password = "old_password"
        context, request = root, DummyRequest(post={"submit": "submit"})
        self.user.active = False
        self.user.last_login_date = None
        res = set_password(context, request)

        assert self.user.confirm_token == "mytoken"
        assert self.user.last_login_date is None
        assert not get_principals().validate_password("mypassword", self.user.password)
        assert not request.is_response(res)

    def test_success_continue(self, root):
        from kotti.views.login import set_password

        self.form_values(
            {
                "token": "mytoken",
                "email": "myemail",
                "password": "mypassword",
                "continue_to": "http://example.com/here#there",
            }
        )
        self.user.confirm_token = "mytoken"
        context, request = root, DummyRequest(post={"submit": "submit"})
        res = set_password(context, request)

        assert res.status == "302 Found"
        assert res.location == "http://example.com/here#there"


class TestUserManageForm:
    def test_schema_factory(self, root):
        from kotti.views.users import UserManageFormView

        request = DummyRequest()
        view = UserManageFormView(root, request)

        schema = view.schema_factory()
        assert "name" not in schema
        assert "password" in schema

    def test_form(self, root):
        from kotti.views.users import UserManageFormView

        request = DummyRequest()
        form = UserManageFormView(root, request)()
        assert 'input type="password"' in form["form"]

    def test_hashed_password_save(self, root):
        from kotti.views.users import UserManageFormView

        user = Mock()
        request = DummyRequest()
        view = UserManageFormView(user, request)
        appstruct = {"password": "foo"}
        view.save_success(appstruct)
        assert user.password.startswith("$2a$10$")

    def test_hashed_password_empty(self, root):
        from kotti.views.users import UserManageFormView

        user = Mock(password="before")
        request = DummyRequest()
        view = UserManageFormView(user, request)
        appstruct = {"password": ""}
        view.save_success(appstruct)
        assert user.password == "before"

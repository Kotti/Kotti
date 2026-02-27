import mock  # must not ``from mock import call``, causes memory error.

from kotti.testing import DummyRequest


class TestRegister:
    def test_register_form(self, root):
        from kotti.views.login import register

        request = DummyRequest()
        res = register(root, request)
        assert res["form"][:5] == "<form"

    def test_register_submit_empty(self, root):
        from kotti.views.login import register

        request = DummyRequest()
        request.POST["register"] = "register"
        res = register(root, request)
        assert "There was a problem with your submission" in res["form"]

    def test_register_submit(self, root):
        from kotti.views.login import register
        from pyramid.httpexceptions import HTTPFound

        request = DummyRequest()
        request.POST["title"] = "Test User"
        request.POST["name"] = "test"
        request.POST["email"] = "test@example.com"
        request.POST["register"] = ("register",)

        with mock.patch("kotti.views.login.UserAddFormView") as form:
            with mock.patch("kotti.views.login.get_principals"):
                res = register(root, request)
                form.assert_has_calls(
                    [
                        mock.call().add_user_success(
                            {
                                "name": "test",
                                "roles": "",
                                "title": "Test User",
                                "send_email": True,
                                "groups": "",
                                "email": "test@example.com",
                            }
                        )
                    ]
                )
        assert isinstance(res, HTTPFound)

    def test_register_event(self, root):
        from kotti.views.login import register

        request = DummyRequest()
        request.POST["title"] = "Test User"
        request.POST["name"] = "test"
        request.POST["email"] = "test@example.com"
        request.POST["register"] = ("register",)

        with mock.patch("kotti.views.login.UserAddFormView"):
            with mock.patch("kotti.views.login.get_principals"):
                with mock.patch("kotti.views.login.notify") as notify:
                    register(root, request)
        assert notify.call_count == 1

    def test_register_submit_groups_and_roles(self, root):
        from kotti.views.login import register
        from pyramid.httpexceptions import HTTPFound

        request = DummyRequest()
        request.POST["title"] = "Test User"
        request.POST["name"] = "test"
        request.POST["email"] = "test@example.com"
        request.POST["register"] = ("register",)

        with mock.patch("kotti.views.login.UserAddFormView") as form:
            with mock.patch("kotti.views.login.get_principals"):
                with mock.patch(
                    "kotti.views.login.get_settings"
                ) as get_settings:  # noqa
                    get_settings.return_value = {
                        "kotti.register.group": "mygroup",
                        "kotti.register.role": "myrole",
                    }

                    res = register(root, request)

        form.assert_has_calls(
            [
                mock.call().add_user_success(
                    {
                        "name": "test",
                        "roles": {"role:myrole"},
                        "title": "Test User",
                        "send_email": True,
                        "groups": ["mygroup"],
                        "email": "test@example.com",
                    }
                )
            ]
        )
        assert isinstance(res, HTTPFound)


class TestNotRegister:
    def test_it(self, app):
        res = app.post("/register", status=404)
        assert res.status == "404 Not Found"

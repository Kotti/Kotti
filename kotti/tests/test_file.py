from io import BytesIO

import pytest
from colander import null
from mock import MagicMock
from mock import patch
from pyramid.httpexceptions import HTTPMovedPermanently

from kotti.filedepot import StoredFileResponse
from kotti.testing import DummyRequest
from kotti.testing import asset
from kotti.views.file import attachment_view
from kotti.views.file import inline_view


class TestFileViews:
    def _create_file(self, config):
        from kotti.resources import File

        self.file = File(asset("logo.png").read(), "myfüle.png", "image/png")

    def _test_common_headers(self, headers):
        for name in ("Content-Disposition", "Content-Length", "Content-Type"):
            assert isinstance(headers[name], str)
        assert headers["Content-Length"] == "55715"
        assert headers["Content-Type"] == "image/png"

    @pytest.mark.parametrize(
        "params", [(inline_view, "inline"), (attachment_view, "attachment")]
    )
    def test_file_views(self, params, config, filedepot, dummy_request, depot_tween):
        view, disposition = params
        self._create_file(config)

        res = view(self.file, dummy_request)

        self._test_common_headers(res.headers)

        assert res.content_disposition.startswith(
            f"{disposition};filename=\"my"
        )

        data = asset("logo.png").read()
        assert res.body == data
        assert b"".join(res.app_iter) == data


class TestFileEditForm:
    def make_one(self):
        from kotti.views.edit.content import FileEditForm
        from kotti.resources import File

        return FileEditForm(File(), DummyRequest())

    def test_edit_with_file(self, db_session, filedepot):
        view = self.make_one()
        view.edit(
            title="A title",
            description="A description",
            tags=["A tag"],
            file=dict(
                fp=BytesIO(b"filecontents"),
                filename="myfile.png",
                mimetype="image/png",
                size=10,
                uid="randomabc",
            ),
        )
        assert view.context.title == "A title"
        assert view.context.description == "A description"
        assert view.context.data.file.read() == b"filecontents"
        assert view.context.filename == "myfile.png"
        assert view.context.mimetype == "image/png"
        assert view.context.size == len(b"filecontents")
        assert view.context.tags == ["A tag"]

    def test_edit_without_file(self, filedepot):
        view = self.make_one()
        view.context.data = b"filecontents"
        view.context.filename = "myfile.png"
        view.context.mimetype = "image/png"
        view.context.size = 777
        with patch("kotti.views.edit.content._to_fieldstorage") as tfs:
            view.edit(title="A title", description="A description", tags=[], file=null)
            assert tfs.call_count == 0
            assert view.context.title == "A title"
            assert view.context.description == "A description"
            assert view.context.data.file.read() == b"filecontents"
            assert view.context.filename == "myfile.png"
            assert view.context.mimetype == "image/png"
            assert view.context.size == 777


class TestFileAddForm:
    def make_one(self):
        from kotti.views.edit.content import FileAddForm

        return FileAddForm(MagicMock(), DummyRequest())

    def test_add(self, config, filedepot):
        view = self.make_one()
        file = view.add(
            title="A title",
            description="A description",
            tags=[],
            file=dict(
                fp=BytesIO(b"filecontents"),
                filename="myfile.png",
                mimetype="image/png",
                size=None,
                uid="randomabc",
            ),
        )

        assert file.title == "A title"
        assert file.description == "A description"
        assert file.tags == []
        assert file.data.file.read() == b"filecontents"
        assert file.filename == "myfile.png"
        assert file.mimetype == "image/png"
        assert file.size == len(b"filecontents")


class TestFileUploadTempStore:
    def make_one(self):
        from kotti.views.form import FileUploadTempStore

        return FileUploadTempStore(DummyRequest())

    def test_keys(self):
        tmpstore = self.make_one()
        tmpstore.session["important"] = 3
        tmpstore.session["_secret"] = 4
        assert tmpstore.keys() == ["important"]

    def test_delitem(self):
        tmpstore = self.make_one()
        tmpstore.session["important"] = 3
        del tmpstore["important"]
        assert "important" not in tmpstore.session

    def test_setitem_with_stream(self):
        ts = self.make_one()
        ts["a"] = {"fp": BytesIO(b"test"), "marker": "yes"}
        assert ts.session["a"] == {"file_contents": b"test", "marker": "yes"}
        v = ts["a"]
        assert "fp" in v.keys()
        assert v["marker"] == "yes"
        assert v["fp"].read() == b"test"

    def test_setitem_with_empty(self):
        ts = self.make_one()
        ts["a"] = {"fp": None, "marker": "yes"}
        assert ts.session["a"] == {"file_contents": b"", "marker": "yes"}
        assert ts["a"] == {"fp": None, "marker": "yes"}


class TestDepotStore:

    from kotti.resources import File

    @pytest.mark.parametrize("factory", [File])
    def test_create(self, factory, filedepot, image_asset, app):
        data = image_asset.read()
        f = factory(data)
        if factory.__class__.__name__ == "File":
            assert len(f.data["files"]) == 1
        elif factory.__class__.__name__ == "Image":
            assert len(f.data["files"]) == 4
        assert f.data.file.read() == data

    @pytest.mark.parametrize("factory", [File])
    def test_edit_content(
        self, factory, filedepot, image_asset, image_asset2, app, db_session
    ):
        data = image_asset.read()
        f = factory(data)
        assert f.data.file.read() == data
        db_session.flush()
        data2 = image_asset2.read()
        f.data = data2
        db_session.flush()

        assert f.data.file.read() == data2

    @pytest.mark.parametrize("factory", [File])
    def test_session_rollback(self, factory, db_session, filedepot, image_asset, app):
        storage = filedepot.get()

        f = factory(data=image_asset.read(), name="content", title="content")
        id = f.data["file_id"]

        db_session.add(f)
        db_session.flush()
        storage.get(id)

        db_session.rollback()
        with pytest.raises(IOError):
            storage.get(id)
        assert storage.delete.called

    @pytest.mark.parametrize("factory", [File])
    def test_delete(self, factory, db_session, root, filedepot, image_asset, app):

        storage = filedepot.get()

        f = factory(data=image_asset, name="content", title="content")
        id = f.data["file_id"]
        root[str(id)] = f
        db_session.flush()

        storage.get(id)

        del root[str(id)]
        import transaction

        transaction.commit()

        with pytest.raises(IOError):
            storage.get(id)
        assert storage.delete.called


class TestUploadedFileResponse:
    def _create_file(
        self, data=b"file contents", filename="myfüle.png", mimetype="image/png"
    ):
        from kotti.resources import File

        return File(data, filename, mimetype)

    def test_as_body(self, filedepot, image_asset, dummy_request):
        data = image_asset.read()
        f = self._create_file(data)
        # resp = UploadedFileResponse(f.data, DummyRequest())
        resp = dummy_request.uploaded_file_response(f.data)
        assert resp.body == data

    def test_as_app_iter(self, filedepot, image_asset, dummy_request):
        from pyramid.response import FileIter

        data = image_asset.read()
        f = self._create_file(data)
        # resp = UploadedFileResponse(f.data, DummyRequest())
        resp = dummy_request.uploaded_file_response(f.data)
        assert isinstance(resp.app_iter, FileIter)
        assert b"".join(resp.app_iter) == data

    def test_unknown_filename(self, filedepot, image_asset2, dummy_request):
        f = self._create_file(b"foo", "file.bar", None)
        # resp = UploadedFileResponse(f.data, DummyRequest())
        resp = dummy_request.uploaded_file_response(f.data)
        assert resp.headers["Content-Type"] == "application/octet-stream"

    def test_guess_content_type(self, filedepot, image_asset, dummy_request):
        f = self._create_file(image_asset.read(), "file.png", None)
        # resp = UploadedFileResponse(f.data, DummyRequest())
        resp = dummy_request.uploaded_file_response(f.data)
        assert resp.headers["Content-Type"] == "image/png"

    def test_caching(self, filedepot, monkeypatch, dummy_request):
        import datetime
        import webob.response

        f = self._create_file()
        d = datetime.datetime(2012, 12, 31, 13)

        class mockdatetime:
            @staticmethod
            def utcnow():
                return d

        monkeypatch.setattr(webob.response, "datetime", mockdatetime)

        # resp = UploadedFileResponse(f.data, DummyRequest(), cache_max_age=10)
        resp = dummy_request.uploaded_file_response(f.data, cache_max_age=10)

        # this is set by filedepot fixture
        assert resp.headers["Last-Modified"] == "Sun, 30 Dec 2012 00:00:00 GMT"
        assert resp.headers["Expires"] == "Mon, 31 Dec 2012 13:00:10 GMT"

    def test_redirect(self, filedepot, dummy_request):
        class PublicFile:
            public_url = "http://example.com"

        class PublicData:
            file = PublicFile()

        with pytest.raises(HTTPMovedPermanently) as e:
            # UploadedFileResponse(PublicData(), DummyRequest())
            dummy_request.uploaded_file_response(PublicData())

        response = e.value
        assert response.headers["Location"] == "http://example.com"


class TestStoredFileResponse:
    def _create_file(
        self, data=b"file contents", filename="myfüle.png", mimetype="image/png"
    ):
        from kotti.resources import File

        return File(data, filename, mimetype)

    def test_as_body(self, filedepot, image_asset, dummy_request):
        data = image_asset.read()
        f = self._create_file(data)
        resp = StoredFileResponse(f.data.file, dummy_request)
        assert resp.body == data

    def test_as_app_iter(self, filedepot, image_asset, dummy_request):
        from pyramid.response import FileIter

        data = image_asset.read()
        f = self._create_file(data)
        resp = StoredFileResponse(f.data.file, dummy_request)
        assert isinstance(resp.app_iter, FileIter)
        assert b"".join(resp.app_iter) == data

    def test_unknown_filename(self, filedepot, image_asset2, dummy_request):
        f = self._create_file(b"foo", "file.bar", None)
        resp = StoredFileResponse(f.data.file, dummy_request)
        assert resp.headers["Content-Type"] == "application/octet-stream"

    def test_guess_content_type(self, filedepot, image_asset, dummy_request):
        f = self._create_file(image_asset.read(), "file.png", None)
        resp = StoredFileResponse(f.data.file, dummy_request)
        assert resp.headers["Content-Type"] == "image/png"

    def test_caching(self, filedepot, monkeypatch, dummy_request):
        import datetime
        import webob.response

        f = self._create_file()
        d = datetime.datetime(2012, 12, 31, 13)

        class mockdatetime:
            @staticmethod
            def utcnow():
                return d

        monkeypatch.setattr(webob.response, "datetime", mockdatetime)

        resp = dummy_request.uploaded_file_response(f.data)
        assert resp.headers["Expires"] == "Mon, 07 Jan 2013 13:00:00 GMT"

        resp = dummy_request.uploaded_file_response(f.data, cache_max_age=10)
        assert resp.headers["Expires"] == "Mon, 31 Dec 2012 13:00:10 GMT"

        # this is set by filedepot fixture
        assert resp.headers["Last-Modified"] == "Sun, 30 Dec 2012 00:00:00 GMT"

    def test_redirect(self, filedepot, dummy_request):
        class PublicFile:
            public_url = "http://example.com"

        with pytest.raises(HTTPMovedPermanently) as e:
            StoredFileResponse(PublicFile(), dummy_request)

        response = e.value
        assert response.headers["Location"] == "http://example.com"

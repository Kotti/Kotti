# -*- coding: utf-8 -*-

from StringIO import StringIO
from colander import null
from pyramid.httpexceptions import HTTPMovedPermanently

from mock import MagicMock
import pytest

from kotti.testing import DummyRequest
from kotti.testing import asset
from kotti.views.file import inline_view
from kotti.views.file import attachment_view
from kotti.views.file import UploadedFileResponse
from kotti.filedepot import StoredFileResponse


class TestFileViews:
    def _create_file(self, config):
        from kotti.resources import File
        self.file = File(asset('logo.png').read(), u"myfüle.png", u"image/png")

    def _test_common_headers(self, headers):
        for name in ('Content-Disposition', 'Content-Length', 'Content-Type'):
            assert isinstance(headers[name], str)
        assert headers["Content-Length"] == "55715"
        assert headers["Content-Type"] == "image/png"

    @pytest.mark.parametrize("params",
                             [(inline_view, 'inline'),
                              (attachment_view, 'attachment')])
    def test_file_views(self, params, config, filedepot, dummy_request,
                        depot_tween):
        from kotti.filedepot import TweenFactory

        view, disposition = params
        self._create_file(config)

        res = view(self.file, dummy_request)

        self._test_common_headers(res.headers)

        assert res.content_disposition.startswith(
            '{0}; filename=my'.format(disposition))

        assert res.app_iter.file.read() == asset('logo.png').read()
        res.app_iter.file.seek(0)
        assert res.body == asset('logo.png').read()


class TestFileEditForm:
    def make_one(self):
        from kotti.views.edit.content import FileEditForm
        from kotti.resources import File

        return FileEditForm(File(), DummyRequest())

    def test_edit_with_file(self, db_session, filedepot):
        view = self.make_one()
        view.edit(
            title=u'A title', description=u'A description',
            tags=[u"A tag"],
            file=dict(
                fp=StringIO('filecontents'),
                filename=u'myfile.png',
                mimetype=u'image/png',
                size=10,
                uid="randomabc",
                ),
            )
        assert view.context.title == u'A title'
        assert view.context.description == u'A description'
        assert view.context.data.file.read() == 'filecontents'
        assert view.context.filename == u'myfile.png'
        assert view.context.mimetype == u'image/png'
        assert view.context.size == len('filecontents')
        assert view.context.tags == [u"A tag"]

    def test_edit_without_file(self, filedepot):
        view = self.make_one()
        view.context.data = 'filecontents'
        view.context.filename = u'myfile.png'
        view.context.mimetype = u'image/png'
        view.context.size = 777
        view.edit(title=u'A title',
                  description=u'A description',
                  tags=[],
                  file=null)
        assert view.context.title == u'A title'
        assert view.context.description == u'A description'
        assert view.context.data.file.read() == 'filecontents'
        assert view.context.filename == u'myfile.png'
        assert view.context.mimetype == u'image/png'
        assert view.context.size == 777


class TestFileAddForm:
    def make_one(self):
        from kotti.views.edit.content import FileAddForm
        return FileAddForm(MagicMock(), DummyRequest())

    def test_add(self, config, filedepot):
        view = self.make_one()
        file = view.add(
            title=u'A title',
            description=u'A description',
            tags=[],
            file=dict(
                fp=StringIO('filecontents'),
                filename=u'myfile.png',
                mimetype=u'image/png',
                size=None,
                uid="randomabc",
                ),
            )

        assert file.title == u'A title'
        assert file.description == u'A description'
        assert file.tags == []
        assert file.data.file.read() == 'filecontents'
        assert file.filename == u'myfile.png'
        assert file.mimetype == u'image/png'
        assert file.size == len('filecontents')


class TestFileUploadTempStore:
    def make_one(self):
        from kotti.views.form import FileUploadTempStore
        return FileUploadTempStore(DummyRequest())

    def test_keys(self):
        tmpstore = self.make_one()
        tmpstore.session['important'] = 3
        tmpstore.session['_secret'] = 4
        assert tmpstore.keys() == ['important']

    def test_delitem(self):
        tmpstore = self.make_one()
        tmpstore.session['important'] = 3
        del tmpstore['important']
        assert 'important' not in tmpstore.session


class TestDepotStore:

    from kotti.resources import File, Image

    @pytest.mark.parametrize("factory", [File, Image])
    def test_create(self, factory, filedepot, image_asset, app):
        data = image_asset.read()
        f = factory(data)
        if factory.__class__.__name__ == 'File':
            assert len(f.data['files']) == 1
        elif factory.__class__.__name__ == 'Image':
            assert len(f.data['files']) == 4
        assert f.data.file.read() == data

    @pytest.mark.parametrize("factory", [File, Image])
    def test_edit_content(self, factory, filedepot, image_asset, image_asset2,
                          app, db_session):
        data = image_asset.read()
        f = factory(data)
        assert f.data.file.read() == data
        db_session.flush()
        data2 = image_asset2.read()
        f.data = data2
        db_session.flush()

        assert f.data.file.read() == data2

    @pytest.mark.parametrize("factory", [File, Image])
    def test_session_rollback(self, factory, db_session, filedepot, image_asset,
                              app):
        from depot.manager import DepotManager

        f = factory(data=image_asset.read(), name=u'content', title=u'content')
        id = f.data['file_id']

        db_session.add(f)
        db_session.flush()
        assert id in DepotManager.get()._storage.keys()

        db_session.rollback()
        assert id not in DepotManager.get()._storage.keys()
        assert DepotManager.get().delete.called

    @pytest.mark.parametrize("factory", [File, Image])
    def test_delete(self, factory, db_session, root, filedepot, image_asset,
                    app):
        from depot.manager import DepotManager

        f = factory(data=image_asset, name=u'content', title=u'content')
        id = f.data['file_id']
        root[str(id)] = f
        db_session.flush()

        assert id in DepotManager.get()._storage.keys()

        del root[str(id)]
        import transaction
        transaction.commit()

        assert DepotManager.get().delete.called
        assert id not in DepotManager.get()._storage.keys()


class TestUploadedFileResponse:
    def _create_file(self,
                     data="file contents",
                     filename=u"myfüle.png",
                     mimetype=u"image/png"):
        from kotti.resources import File
        return File(data, filename, mimetype)

    def test_as_body(self, filedepot, image_asset):
        data = image_asset.read()
        f = self._create_file(data)
        resp = UploadedFileResponse(f.data, DummyRequest())
        assert resp.body == data

    def test_as_app_iter(self, filedepot, image_asset):
        from pyramid.response import FileIter
        data = image_asset.read()
        f = self._create_file(data)
        resp = UploadedFileResponse(f.data, DummyRequest())
        assert isinstance(resp.app_iter, FileIter)
        assert ''.join(resp.app_iter) == data

    def test_unknown_filename(self, filedepot, image_asset2):
        f = self._create_file(b'foo', u"file.bar", None)
        resp = UploadedFileResponse(f.data, DummyRequest())
        assert resp.headers['Content-Type'] == 'application/octet-stream'

    def test_guess_content_type(self, filedepot, image_asset):
        f = self._create_file(image_asset.read(), u"file.png", None)
        resp = UploadedFileResponse(f.data, DummyRequest())
        assert resp.headers['Content-Type'] == 'image/png'

    def test_caching(self, filedepot, monkeypatch):
        import datetime
        import webob.response

        f = self._create_file()
        d = datetime.datetime(2012, 12, 31, 13)

        class mockdatetime:
            @staticmethod
            def utcnow():
                return d

        monkeypatch.setattr(webob.response, 'datetime', mockdatetime)

        resp = UploadedFileResponse(f.data, DummyRequest(), cache_max_age=10)

        # this is set by filedepot fixture
        assert resp.headers['Last-Modified'] == 'Sun, 30 Dec 2012 00:00:00 GMT'
        assert resp.headers['Expires'] == 'Mon, 31 Dec 2012 13:00:10 GMT'

    def test_redirect(self, filedepot):

        class PublicFile(object):
            public_url = 'http://example.com'

        class PublicData(object):
            file = PublicFile()

        with pytest.raises(HTTPMovedPermanently) as e:
            UploadedFileResponse(PublicData(), DummyRequest())

        response = e.value
        assert response.headers['Location'] == 'http://example.com'


class TestStoredFileResponse:
    def _create_file(self,
                     data="file contents",
                     filename=u"myfüle.png",
                     mimetype=u"image/png"):
        from kotti.resources import File
        return File(data, filename, mimetype)

    def test_as_body(self, filedepot, image_asset):
        data = image_asset.read()
        f = self._create_file(data)
        resp = StoredFileResponse(f.data.file, DummyRequest())
        assert resp.body == data

    def test_as_app_iter(self, filedepot, image_asset):
        from pyramid.response import FileIter
        data = image_asset.read()
        f = self._create_file(data)
        resp = StoredFileResponse(f.data.file, DummyRequest())
        assert isinstance(resp.app_iter, FileIter)
        assert ''.join(resp.app_iter) == data

    def test_unknown_filename(self, filedepot, image_asset2):
        f = self._create_file(b'foo', u"file.bar", None)
        resp = StoredFileResponse(f.data.file, DummyRequest())
        assert resp.headers['Content-Type'] == 'application/octet-stream'

    def test_guess_content_type(self, filedepot, image_asset):
        f = self._create_file(image_asset.read(), u"file.png", None)
        resp = StoredFileResponse(f.data.file, DummyRequest())
        assert resp.headers['Content-Type'] == 'image/png'

    def test_caching(self, filedepot, monkeypatch):
        import datetime
        import webob.response

        f = self._create_file()
        d = datetime.datetime(2012, 12, 31, 13)

        class mockdatetime:
            @staticmethod
            def utcnow():
                return d

        monkeypatch.setattr(webob.response, 'datetime', mockdatetime)

        resp = StoredFileResponse(f.data.file, DummyRequest(), cache_max_age=10)

        # this is set by filedepot fixture
        assert resp.headers['Last-Modified'] == 'Sun, 30 Dec 2012 00:00:00 GMT'
        assert resp.headers['Expires'] == 'Mon, 31 Dec 2012 13:00:10 GMT'

    def test_redirect(self, filedepot):
        class PublicFile(object):
            public_url = 'http://example.com'

        with pytest.raises(HTTPMovedPermanently) as e:
            StoredFileResponse(PublicFile(), DummyRequest())

        response = e.value
        assert response.headers['Location'] == 'http://example.com'

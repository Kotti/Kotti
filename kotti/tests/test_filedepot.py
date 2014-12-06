import datetime

class TestDBStoredFile:

    def test_content_length(self, db_session, events, setup_app):
        from kotti.filedepot import DBStoredFile

        f = DBStoredFile('fileid', data="content")
        db_session.add(f)
        db_session.flush()
        assert f.content_length == 7
        f.data = 'content changed'
        db_session.flush()
        assert f.content_length == len('content changed')

    def test_last_modified(self, monkeypatch, db_session, events, setup_app):
        from kotti.filedepot import DBStoredFile
        from kotti import filedepot

        now = datetime.datetime.now()

        class mockdatetime:
            @staticmethod
            def now():
                return now

        monkeypatch.setattr(filedepot, 'datetime', mockdatetime)

        f = DBStoredFile('fileid', data="content")
        db_session.add(f)
        db_session.flush()

        assert f.last_modified == now

        f.last_modified = None
        f.data = 'content changed'
        db_session.flush()

        assert f.last_modified == now

    def test_storedfile_interface(self):
        from kotti.filedepot import DBStoredFile

        f = DBStoredFile('fileid', filename='f.jpg', content_type='image/jpeg',
                         content_length=1000, data='content')

        assert f.close() == None
        assert f.closed() == False
        assert f.seekable() == False
        assert f.writable() == False

        assert f.read() == 'content'
        assert f.read(-1) == 'content'
        assert f.read(0) == ''
        assert f.read(2) == 'co'
        assert f.read(4) == 'cont'

        assert f.content_length == 1000
        assert f.content_type == 'image/jpeg'
        assert f.file_id == 'fileid'
        assert f.filename == 'f.jpg'
        assert f.name == "f.jpg"
        assert f.public_url == None

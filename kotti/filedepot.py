import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy import event
from sqlalchemy.orm import deferred

from depot.io.interfaces import FileStorage

from kotti import Base
from kotti import DBSession

_marker = object()


class DBStoredFile(Base):
    """depotfile StoredFile implementation that stores data in the db.

    Can be used together with DBFileStorage to implement blobs (large files)
    storage in the database.
    """

    __tablename__ = "blobs"

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), primary_key=True)
    #: Unique id given to this blob
    #: (:class:`sqlalchemy.types.String`)
    file_id = Column(String(36), index=True)
    #: The original filename it had when it was uploaded.
    #: (:class:`sqlalchemy.types.String`)
    filename = Column(Unicode(100))
    #: MIME type of the blob
    #: (:class:`sqlalchemy.types.String`)
    content_type = Column(String(100))
    #: Size of the blob in bytes
    #: (:class:`sqlalchemy.types.Integer`)
    content_length = Column(Integer())
    #: Date / time the blob was created
    #: (:class:`sqlalchemy.types.DateTime`)
    last_modified = Column(DateTime())
    #: The binary data itself
    #: (:class:`sqlalchemy.types.LargeBinary`)
    data = deferred(Column('data', LargeBinary()))

    _cursor = 0
    _data = _marker

    def __init__(self, file_id, filename=None, content_type=None,
                 last_modified=None, content_length=None, **kwds):
        self.file_id = file_id
        self.filename = filename
        self.content_type = content_type
        self.last_modified = last_modified
        self.content_length = content_length

        for k, v in kwds.items():
            setattr(self, k, v)

    def read(self, n=-1):
        """Reads ``n`` bytes from the file.

        If ``n`` is not specified or is ``-1`` the whole
        file content is read in memory and returned
        """
        if self._data is _marker:
            file_id = DBSession.merge(self).file_id
            self._data = DBSession.query(DBStoredFile.data).\
                filter_by(file_id=file_id).scalar()

        if n == -1:
            result = self._data[self._cursor:]
        else:
            result = self._data[self._cursor:self._cursor + n]

        self._cursor += len(result)

        return result

    def close(self, *args, **kwargs):
        """Implement :meth:`StoredFile.close`.
        :class:`DBStoredFile` never closes.
        """
        return

    def closed(self):
        """Implement :meth:`StoredFile.closed`.
        """
        return False

    def writable(self):
        """Implement :meth:`StoredFile.writable`.
        """
        return False

    def seekable(self):
        """Implement :meth:`StoredFile.seekable`.
        """
        return True

    def seek(self, n):
        self._cursor = n

    def tell(self):
        return self._cursor

    @property
    def name(self):
        """Implement :meth:`StoredFile.name`.

        This is the filename of the saved file
        """
        return self.filename

    @property
    def public_url(self):
        """The public HTTP url from which file can be accessed.

        When supported by the storage this will provide the
        public url to which the file content can be accessed.
        In case this returns ``None`` it means that the file can
        only be served by the :class:`DepotMiddleware` itself.
        """
        return None

    @classmethod
    def refresh_data(cls, target, value, oldvalue, initiator):
        target._cursor = 0
        target._data = _marker

    @classmethod
    def __declare_last__(cls):
        # For the ``data`` column, use the field value setter from filedepot.
        # filedepot already registers this event listener, but it does so in a
        # way that won't work properly for subclasses of File

        event.listen(DBStoredFile.data, 'set', DBStoredFile.refresh_data)


def set_metadata(event):
    """Set DBStoredFile metadata based on data

    :param event: event that trigerred this handler.
    :type event: :class:`ObjectInsert` or :class:`ObjectUpdate`
    """
    obj = event.object
    obj.content_length = obj.data and len(obj.data) or 0
    obj.last_modified = datetime.now()


class DBFileStorage(FileStorage):
    """Implementation of :class:`depot.io.interfaces.FileStorage`,

    Uses `kotti.filedepot.DBStoredFile` to store blob data in an SQL database.
    """

    def get(self, file_id):
        """Returns the file given by the file_id
        """

        f = DBSession.query(DBStoredFile).filter_by(file_id=file_id).first()
        if f is None:
            raise IOError
        return f

    def create(self, content, filename=None, content_type=None):
        """Saves a new file and returns the file id

        ``content`` parameter can either be ``bytes``, another ``file object``
        or a :class:`cgi.FieldStorage`. When ``filename`` and ``content_type``
        parameters are not provided they are deducted from the content itself.
        """
        new_file_id = str(uuid.uuid1())
        content, filename, content_type = self.fileinfo(
            content, filename, content_type)
        if hasattr(content, 'read'):
            content = content.read()

        fstore = DBStoredFile(data=content,
                              file_id=new_file_id,
                              filename=filename,
                              content_type=content_type,
                              )
        DBSession.add(fstore)
        return new_file_id

    def replace(self, file_or_id, content, filename=None, content_type=None):
        """Replaces an existing file, an ``IOError`` is raised if the file
        didn't already exist.

        Given a :class:`StoredFile` or its ID it will replace the current
        content with the provided ``content`` value. If ``filename`` and
        ``content_type`` are provided or can be deducted by the ``content``
        itself they will also replace the previous values, otherwise the current
        values are kept.
        """

        file_id = self._get_file_id(file_or_id)

        content, filename, content_type = self.fileinfo(
            content, filename, content_type)

        fstore = self.get(file_id)

        if filename is not None:
            fstore.filename = filename
        if content_type is not None:
            fstore.content_type = content_type

        if hasattr(content, 'read'):
            content = content.read()

        fstore.data = content

    def delete(self, file_or_id):
        """Deletes a file. If the file didn't exist it will just do nothing."""

        file_id = self._get_file_id(file_or_id)

        DBSession.query(DBStoredFile).filter_by(file_id=file_id).delete()

    def exists(self, file_or_id):
        """Returns if a file or its ID still exist."""

        file_id = self._get_file_id(file_or_id)

        return bool(
            DBSession.query(DBStoredFile).filter_by(file_id=file_id).count())

    def _get_file_id(self, file_or_id):
        if hasattr(file_or_id, 'file_id'):
            return file_or_id.file_id
        return file_or_id


def configure_filedepot(settings):
    from kotti.util import flatdotted_to_dict
    from depot.manager import DepotManager

    config = flatdotted_to_dict('kotti.depot.', settings)
    for name, conf in config.items():
        if DepotManager.get(name) is None:
            DepotManager.configure(name, conf, prefix='')


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """
    from kotti.events import objectevent_listeners
    from kotti.events import ObjectInsert
    from kotti.events import ObjectUpdate
    from depot.fields.sqlalchemy import _SQLAMutationTracker

    configure_filedepot(config.get_settings())

    # Update file metadata on change of blob data
    objectevent_listeners[
        (ObjectInsert, DBStoredFile)].append(set_metadata)
    objectevent_listeners[
        (ObjectUpdate, DBStoredFile)].append(set_metadata)

    # depot's _SQLAMutationTracker._session_committed is executed on
    # after_commit, that's too late for DBFileStorage to interact with the
    # session
    event.listen(DBSession,
                 'before_commit',
                 _SQLAMutationTracker._session_committed)

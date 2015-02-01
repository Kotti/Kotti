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
from kotti.util import camel_case_to_name
from kotti.util import command

_marker = object()


class DBStoredFile(Base):
    """ :class:`depot.io.interfaces.StoredFile` implementation that stores
    file data in SQL database.

    Can be used together with :class:`kotti.filedepot.DBFileStorage` to
    implement blobs storage in the database.
    """

    __tablename__ = "blobs"

    #: Primary key column in the DB
    #: (:class:`sqlalchemy.types.Integer`)
    id = Column(Integer(), primary_key=True)
    #: Unique file id given to this blob
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
    #: Date / time the blob was created or last modified
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
        self.last_modified = last_modified or datetime.now()
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
        """ Move the file cursor to position `n`

        :param n: Position for the cursor
        :type n: int
        """
        self._cursor = n

    def tell(self):
        """ Returns current position of file cursor

        :result: Current file cursor position.
        :rtype: int
        """
        return self._cursor

    @property
    def name(self):
        """Implement :meth:`StoredFile.name`.

        :result: the filename of the saved file
        :rtype: string
        """
        return self.filename

    @property
    def public_url(self):
        """ Integration with :class:`depot.middleware.DepotMiddleware`

        When supported by the storage this will provide the
        public url to which the file content can be accessed.
        In case this returns ``None`` it means that the file can
        only be served by the :class:`depot.middleware.DepotMiddleware` itself.
        """
        return None

    @classmethod
    def __declare_last__(cls):
        """ Executed by SQLAlchemy as part of mapper configuration

        When the data changes, we want to reset the cursor position of target
        instance, to allow proper streaming of data.
        """
        event.listen(DBStoredFile.data, 'set', handle_change_data)


def handle_change_data(target, value, oldvalue, initiator):
    target._cursor = 0
    target._data = _marker


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

        :param file_id: the unique id associated to the file
        :type file_id: string
        :result: a :class:`kotti.filedepot.DBStoredFile` instance
        :rtype: :class:`kotti.filedepot.DBStoredFile`
        """

        f = DBSession.query(DBStoredFile).filter_by(file_id=file_id).first()
        if f is None:
            raise IOError
        return f

    def create(self, content, filename=None, content_type=None):
        """Saves a new file and returns the file id

        :param content: can either be ``bytes``, another ``file object``
                        or a :class:`cgi.FieldStorage`. When ``filename`` and
                        ``content_type``  parameters are not provided they are
                        deducted from the content itself.

        :param filename: filename for this file
        :type filename: string

        :param content_type: Mimetype of this file
        :type content_type: string

        :return: the unique ``file_id`` associated to this file
        :rtype: string
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

        :param file_or_id: can be either ``DBStoredFile`` or a ``file_id``

        :param content: can either be ``bytes``, another ``file object``
                        or a :class:`cgi.FieldStorage`. When ``filename`` and
                        ``content_type`` parameters are not provided they are
                        deducted from the content itself.

        :param filename: filename for this file
        :type filename: string

        :param content_type: Mimetype of this file
        :type content_type: string
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
        """Deletes a file. If the file didn't exist it will just do nothing.

        :param file_or_id: can be either ``DBStoredFile`` or a ``file_id``
        """

        file_id = self._get_file_id(file_or_id)

        DBSession.query(DBStoredFile).filter_by(file_id=file_id).delete()

    def exists(self, file_or_id):
        """Returns if a file or its ID still exist.

        :return: Returns if a file or its ID still exist.
        :rtype: bool
        """

        file_id = self._get_file_id(file_or_id)

        return bool(
            DBSession.query(DBStoredFile).filter_by(file_id=file_id).count())

    def _get_file_id(self, file_or_id):
        if hasattr(file_or_id, 'file_id'):
            return file_or_id.file_id
        return file_or_id


def configure_filedepot(settings):
    from kotti.util import extract_depot_settings
    from depot.manager import DepotManager

    config = extract_depot_settings('kotti.depot.', settings)
    for conf in config:
        name = conf.pop('name')
        if name not in DepotManager._depots:
            DepotManager.configure(name, conf, prefix='')


def migrate_storage(from_storage, to_storage):
    from depot.fields.sqlalchemy import _SQLAMutationTracker
    from depot.manager import DepotManager
    from kotti.util import _to_fieldstorage
    import logging

    log = logging.getLogger(__name__)

    old_default = DepotManager._default_depot
    DepotManager._default_depot = to_storage

    for klass, props in _SQLAMutationTracker.mapped_entities.items():
        log.info("Migrating %r", klass)

        mapper = klass._sa_class_manager.mapper

        # use type column to avoid polymorphism issues, getting the same
        # Node item multiple times.
        type_ = camel_case_to_name(klass.__name__)
        for instance in DBSession.query(klass).filter_by(type=type_):
            for prop in props:
                uf = getattr(instance, prop)
                if not uf:
                    continue
                pk = mapper.primary_key_from_instance(instance)
                log.info("Migrating %s for %r with pk %r", prop, klass, pk)

                filename = uf['filename']
                content_type = uf['content_type']
                data = _to_fieldstorage(fp=uf.file,
                                        filename=filename,
                                        mimetype=content_type,
                                        size=uf.file.content_length)
                setattr(instance, prop, data)

    DepotManager._default_depot = old_default


def migrate_storages_command():  # pragma: no cover
    __doc__ = """ Migrate blobs between two configured filedepot storages

    Usage:
      kotti-migrate-storage <config_uri> --from-storage <name> --to-storage <name>

    Options:
      -h --help                 Show this screen.
      --from-storage <name>   The storage name that has blob data to migrate
      --to-storage <name>     The storage name where we want to put the blobs
    """
    return command(
        lambda args: migrate_storage(
            from_storage=args['--from-storage'],
            to_storage=args['--to-storage'],
        ),
        __doc__,
    )


def adjust_for_engine(conn, branch):
    # adjust for engine type

    if conn.engine.dialect.name == 'mysql':  # pragma: no cover
        from sqlalchemy.dialects.mysql.base import LONGBLOB
        DBStoredFile.__table__.c.data.type = LONGBLOB()

    # sqlite's Unicode columns return a buffer which can't be encoded by
    # a json encoder. We have to convert to a unicode string so that the value
    # can be saved corectly by
    # :class:`depot.fields.sqlalchemy.upload.UploadedFile`

    def patched_processed_result_value(self, value, dialect):
        if not value:
            return None
        return self._upload_type.decode(unicode(value))

    if conn.engine.dialect.name == 'sqlite':  # pragma: no cover
        from depot.fields.sqlalchemy import UploadedFileField
        UploadedFileField.process_result_value = patched_processed_result_value


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    from kotti.events import objectevent_listeners
    from kotti.events import ObjectInsert
    from kotti.events import ObjectUpdate
    from depot.fields.sqlalchemy import _SQLAMutationTracker

    from sqlalchemy.event import listen
    from sqlalchemy.engine import Engine

    listen(Engine, 'engine_connect', adjust_for_engine)

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

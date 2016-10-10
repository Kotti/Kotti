# -*- coding: utf-8 -*-
import logging
import mimetypes
import uuid
from datetime import datetime

import rfc6266
from depot.fields.sqlalchemy import _SQLAMutationTracker
from depot.io.interfaces import FileStorage
from depot.manager import DepotManager
from pyramid import tweens
from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import _BLOCK_SIZE
from pyramid.response import FileIter
from pyramid.response import Response
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import event
from sqlalchemy import Integer
from sqlalchemy import LargeBinary
from sqlalchemy import String
from sqlalchemy import Unicode
from sqlalchemy.orm import deferred
from unidecode import unidecode

from kotti import Base, get_settings
from kotti import DBSession
from kotti.util import camel_case_to_name
from kotti.util import command
from kotti.util import extract_from_settings
from kotti.util import _to_fieldstorage

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

    public_url = None

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

    @staticmethod
    def close(*args, **kwargs):
        """Implement :meth:`StoredFile.close`.
        :class:`DBStoredFile` never closes.
        """
        return

    @staticmethod
    def closed():
        """Implement :meth:`StoredFile.closed`.
        """
        return False

    @staticmethod
    def writable():
        """Implement :meth:`StoredFile.writable`.
        """
        return False

    @staticmethod
    def seekable():
        """Implement :meth:`StoredFile.seekable`.
        """
        return True

    def seek(self, offset, whence=0):
        """ Change stream position.

        Change the stream position to the given byte offset. The offset is
        interpreted relative to the position indicated by whence.

        :param offset: Position for the cursor
        :type offset: int

        :param whence: * 0 -- start of stream (the default);
                              offset should be zero or positive
                       * 1 -- current stream position; offset may be negative
                       * 2 -- end of stream; offset is usually negative
        :type whence: int
        """
        if whence == 0:
            self._cursor = offset
        elif whence in (1, 2):
            self._cursor = self._cursor + offset
        else:
            raise ValueError('whence must be 0, 1 or 2')

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

    # noinspection PyMethodOverriding
    @staticmethod
    def get(file_id):
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
        itself they will also replace the previous values, otherwise
        the current values are kept.

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

    @staticmethod
    def list(*args):
        raise NotImplementedError("list() method is unimplemented.")

    @staticmethod
    def _get_file_id(file_or_id):
        if hasattr(file_or_id, 'file_id'):
            return file_or_id.file_id
        return file_or_id


def migrate_storage(from_storage, to_storage):

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


class StoredFileResponse(Response):
    """ A Response object that can be used to serve an UploadedFile instance.

    Code adapted from :class:`pyramid.response.FileResponse`.
    """

    def __init__(self, f, request, disposition='attachment',
                 cache_max_age=604800, content_type=None,
                 content_encoding=None):
        """
        :param f: the ``UploadedFile`` file field value.
        :type f: :class:`depot.io.interfaces.StoredFile`

        :param request: Current request.
        :type request: :class:`pyramid.request.Request`

        :param disposition:
        :type disposition:

        :param cache_max_age: The number of seconds that should be used to HTTP
                              cache this response.

        :param content_type: The content_type of the response.

        :param content_encoding: The content_encoding of the response.
                                 It's generally safe to leave this set to
                                 ``None`` if you're serving a binary file.
                                 This argument will be ignored if you also
                                 leave ``content-type`` as ``None``.
        """

        if f.public_url:
            raise HTTPMovedPermanently(f.public_url)

        content_encoding, content_type = self._get_type_and_encoding(
            content_encoding, content_type, f)

        super(StoredFileResponse, self).__init__(
            conditional_response=True,
            content_type=content_type,
            content_encoding=content_encoding)

        app_iter = None
        if request is not None and \
                not get_settings()['kotti.depot_replace_wsgi_file_wrapper']:
            environ = request.environ
            if 'wsgi.file_wrapper' in environ:
                app_iter = environ['wsgi.file_wrapper'](f, _BLOCK_SIZE)
        if app_iter is None:
            app_iter = FileIter(f)
        self.app_iter = app_iter

        # assignment of content_length must come after assignment of app_iter
        self.content_length = f.content_length
        self.last_modified = f.last_modified

        if cache_max_age is not None:
            self.cache_expires = cache_max_age
            self.cache_control.public = True

        self.etag = self.generate_etag(f)
        self.content_disposition = rfc6266.build_header(
            f.filename, disposition=disposition,
            filename_compat=unidecode(f.filename))

    @staticmethod
    def _get_type_and_encoding(content_encoding, content_type, f):
        content_type = content_type or getattr(f, 'content_type', None)
        if content_type is None:
            content_type, content_encoding = \
                mimetypes.guess_type(f.filename, strict=False)
        if content_type is None:
            content_type = 'application/octet-stream'
        # str-ifying content_type is a workaround for a bug in Python 2.7.7
        # on Windows where mimetypes.guess_type returns unicode for the
        # content_type.
        content_type = str(content_type)
        return content_encoding, content_type

    @staticmethod
    def generate_etag(f):
        return '"{0}-{1}"'.format(f.last_modified, f.content_length)


def uploaded_file_response(self, uploaded_file, disposition='inline'):
    return StoredFileResponse(uploaded_file.file, self,
                              disposition=disposition)


def uploaded_file_url(self, uploaded_file, disposition='inline'):
    if disposition == 'attachment':
        suffix = '/download'
    else:
        suffix = ''
    url = '{0}/{1}/{2}{3}'.format(
        self.application_url,
        get_settings()['kotti.depot_mountpoint'][1:],
        uploaded_file.path,
        suffix)
    return url


class TweenFactory(object):
    """Factory for a Pyramid tween in charge of serving Depot files.

    This is the Pyramid tween version of
    :class:`depot.middleware.DepotMiddleware`.  It does exactly the same as
    Depot's WSGI middleware, but operates on a :class:`pyramid.request.Request`
    object instead of the WSGI environment.
    """

    def __init__(self, handler, registry):
        """
        :param handler: Downstream tween or main Pyramid request handler (Kotti)
        :type handler: function

        :param registry: Application registry
        :type registry: :class:`pyramid.registry.Registry`
        """

        self.mountpoint = registry.settings['kotti.depot_mountpoint']
        self.handler = handler
        self.registry = registry

        DepotManager.set_middleware(self)

    def url_for(self, path):
        return u'/'.join((self.mountpoint, path))

    def __call__(self, request):
        """
        :param request: Current request
        :type request: :class:`kotti.request.Request`

        :return: Respone object
        :rtype: :class:`pyramid.response.Response`
        """

        # Only handle GET and HEAD requests for the mountpoint.
        # All other requests are passed to downstream handlers.
        if request.method not in ('GET', 'HEAD') \
                or not request.path.startswith(self.mountpoint):
            response = self.handler(request)
            return response

        # paths match this pattern
        # /<mountpoint>/<depot name>/<file id>[/download]
        path = request.path.split('/')
        if len(path) and not path[0]:
            path = path[1:]

        if len(path) < 3:
            response = HTTPNotFound()
            return response

        __, depot, fileid = path[:3]
        depot = DepotManager.get(depot)
        if not depot:
            response = HTTPNotFound()
            return response

        try:
            f = depot.get(fileid)
        except (IOError, ValueError):
            response = HTTPNotFound()
            return response

        # if the file has a public_url, it's stored somewhere else (e.g. S3)
        public_url = f.public_url
        if public_url is not None:
            response = HTTPMovedPermanently(public_url)
            return response

        # file is not directly accessible for user agents, serve it ourselves
        if path[-1] == 'download':
            disposition = 'attachment'
        else:
            disposition = 'inline'
        response = StoredFileResponse(f, request, disposition=disposition)
        return response


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


def extract_depot_settings(prefix="kotti.depot.", settings=None):
    """ Merges items from a dictionary that have keys that start with `prefix`
    to a list of dictionaries.

    :param prefix: A dotted string representing the prefix for the common values
    :type prefix: string

    :param settings: A dictionary with settings. Result is extracted from this
    :type settings: dict

      >>> settings = {
      ...     'kotti.depot_mountpoint': '/depot',
      ...     'kotti.depot.0.backend': 'kotti.filedepot.DBFileStorage',
      ...     'kotti.depot.0.file_storage': 'var/files',
      ...     'kotti.depot.0.name': 'local',
      ...     'kotti.depot.1.backend': 'depot.io.gridfs.GridStorage',
      ...     'kotti.depot.1.name': 'mongodb',
      ...     'kotti.depot.1.uri': 'localhost://',
      ... }
      >>> res = extract_depot_settings('kotti.depot.', settings)
      >>> print(sorted(res[0].items()))
      [('backend', 'kotti.filedepot.DBFileStorage'), ('file_storage', 'var/files'), ('name', 'local')]
      >>> print(sorted(res[1].items()))
      [('backend', 'depot.io.gridfs.GridStorage'), ('name', 'mongodb'), ('uri', 'localhost://')]
    """

    extracted = {}
    for k, v in extract_from_settings(prefix, settings).items():
        index, conf = k.split('.', 1)
        index = int(index)
        extracted.setdefault(index, {})
        extracted[index][conf] = v

    result = []
    for k in sorted(extracted.keys()):
        result.append(extracted[k])

    return result


def configure_filedepot(settings):

    config = extract_depot_settings('kotti.depot.', settings)
    for conf in config:
        name = conf.pop('name')
        if name not in DepotManager._depots:
            DepotManager.configure(name, conf, prefix='')


def includeme(config):
    """ Pyramid includeme hook.

    :param config: app config
    :type config: :class:`pyramid.config.Configurator`
    """

    config.add_tween('kotti.filedepot.TweenFactory',
                     over=tweens.MAIN,
                     under=tweens.INGRESS)
    config.add_request_method(uploaded_file_response,
                              name='uploaded_file_response')
    config.add_request_method(uploaded_file_url, name='uploaded_file_url')

    from kotti.events import objectevent_listeners
    from kotti.events import ObjectInsert
    from kotti.events import ObjectUpdate

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

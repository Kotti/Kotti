.. _blobs:

Working with Blob Data in Kotti
===============================

Kotti provides flexible mechanisms for storing and serving blob data by with the help of `Depot`_.

.. contents::

How File-like Content is stored
-------------------------------

Both ``File`` and ``Image`` store their data in :class:`depot.fields.sqlalchemy.UploadedFileField` and they will offload their blob data to the configured depot storage.
Working together with `Depot`_ configured storages means it is possible to store blob data in a variety of ways: filesystem, GridFS, Amazon storage, etc.

- :class:`depot.io.local.LocalFileStorage`
- :class:`depot.io.awss3.S3Storage`
- :class:`depot.io.gridfs.GridFSStorage`
- etc.

By default Kotti will store its blob data in the configured SQL database, using :class:`kotti.filedepot.DBFileStorage` storage, but you can configure your own preferred way of storing your blob data.
The benefit of storing files in :class:`kotti.filedepot.DBFileStorage` is having *all* content in a single place (the DB) which makes backups, exporting and importing of your site's data easy, as long as you don't have too many or too large files.
The downsides of this approach appear when your database server resides on a different host (network performance becomes a greater issue) or your DB dumps become too large to be handled efficiently.

Configuration
-------------

Mountpoint
~~~~~~~~~~

Kotti provides a Pyramid tween (:ref:`pyramid.registering_tweens`) that is responsible for the actual serving of blob data.
It does pretty much the same as :class:`depot.middleware.DepotMiddleware`, but is better integrated into Pyramid and therefore Kotti.

This tween "intercepts" all requests before they reach the main application (Kotti).
If it's a request for blob data (identified by the configured ``kotti.depot_mountpoint``), it will be served by the tween itself (or redirected to an external storage like S3), otherwise it will be "forwarded" to the main application.
This mountpoint is also used to generate URLs to blobs.
The default value for ``kotti.depot_mountpoint`` is ``/depot``::

    kotti.depot_mountpoint = /depot

WSGI File Wrapper
-----------------

In case you have issues serving files with your WSGI server, your can try to set ``kotti.depot_replace_wsgi_file_wrapper = true``.
This forces Kotti to use :class:`pyramid.response.FileIter` instead of the one provided by your WSGI server.

Storages
~~~~~~~~

While `Depot`_ allows storing data in any of the configured filestorages, at this time there's no mechanism in Kotti to select, at runtime, the depot where new data will be saved.
Instead, Kotti will store new files only in the configured ``default`` store.
If, for example, you add a new depot and make that the default, you should leave the old depot configured so that Kotti will continue serving files uploaded there.

By default, Kotti comes configured with a db-based filestorage::

    kotti.depot.0.name = dbfiles
    kotti.depot.0.backend = kotti.filedepot.DBFileStorage

To configure a depot, several ``kotti.depot.*.*`` lines need to be added.
The number in the first position is used to group backend configuration and to order the file storages in the configuration of `Depot`_.
The depot configured with number 0 will be the default depot, where all new blob data will be saved.
There are 2 options that are required for every storage configuration: ``name`` and ``backend``.
The ``name`` is a unique string that will be used to identify the path of saved files (it is recorded with each blob info), so once configured for a particular storage, it should never change.
The ``backend`` should point to a dotted path for the storage class.
Any further parameters for a particular backend will be passed as keyword arguments to the backend class.

See this example, in which we store, by default, files in ``/var/local/files/`` using the :class:`depot.io.local.LocalFileStorage`::

    kotti.depot.0.name = localfs
    kotti.depot.0.backend = depot.io.local.LocalFileStorage
    kotti.depot.0.storage_path = /var/local/files
    kotti.depot.1.name = dbfiles
    kotti.depot.1.backend = kotti.filedepot.DBFileStorage

Notice that we kept the ``dbfiles`` storage, but we moved it to position 1.
No blob data will be saved there anymore, but existing files in that storage will continue to be available from there.

How File-like Content is served
-------------------------------

Starting with Kotti 1.3.0, file-like content can be served in two different ways.
Let's look at an example to compare them.

Say we have a :class:`kotti.resources.File` object in our resource tree, located at ``/foo/bar/file``.

Method 1
~~~~~~~~

In the default views this file is served under the URL ``http://localhost/foo/bar/file/attachment-view``.
This URL can be created like this::

    >>> from kotti.resources import File
    >>> file = File.query.filter(File.name == 'file').one()
    >>> request.resource_url(file, 'attachment-view')
    'http://localhost/foo/bar/file/attachment-view'

When this URL is requested, a :class:`kotti.filedepot.StoredFileResponse` is returned::

    >>> request.uploaded_file_response(file.data)
    <StoredFileResponse at 0x10c8d22d0 200 OK>

The request is processed in the same way as for every other type of content in Kotti.
It goes through the full traversal and view lookup machinery *with full permission checks*.

Method 2
~~~~~~~~

Often these permission checks do not need to be enforced strictly.
For such cases Kotti provides a "shortcut" in form of a Pyramid tween, that directly processes all requests under a certain path befor they even reach Kotti.
This means: no traversal, no view lookup, no permission checks.
The URL for this method can be created very similarily::

    >>> request.uploaded_file_url(file.data, 'attachment')
    'http://localhost//depot/dbfiles/68f31e97-a7f9-11e5-be07-c82a1403e6a7/download'

Comparison
~~~~~~~~~~

Obviously method 2 is *a lot* faster than method 1 - typically at least by the factor of 3.

If you take a look at the callgraphs, you'll understand where this difference comes from:

========== ==========
|m1kotti|_ |m2kotti|_
========== ==========
 Method 1   Method 2
========== ==========

.. |m1kotti| image:: /_static/callgraph-served-by-kotti.svg
   :width: 100%
.. _m1kotti: ../../_static/callgraph-served-by-kotti.svg
.. |m2kotti| image:: /_static/callgraph-served-by-tween.svg
   :width: 100%
.. _m2kotti: ../../_static/callgraph-served-by-tween.svg

The difference will be even more drastic, when you set up proper HTTP caching.
All responses for method 2 can be cached *forever*, because the URL will change when the file's content changes.

Developing (with) File-like Content
-----------------------------------

Add a Blob Field to your Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding a blob data attribute to your models can be as simple as::

    from depot.fields.sqlalchemy import UploadedFileField
    from kotti.resources import Content

    class Person(Content):
        avatar = UploadedFileField()

While you can directly assign a ``bytes`` value to the ``avatar`` column, the ``UploadedFileField`` column type works best when you assign a :class:`cgi.FieldStorage` instance as value::

    from StringIO import StringIO
    from kotti.util import _to_fieldstorage

    content = '...'
    data = {
            'fp': StringIO(content),
            'filename': 'avatar.png',
            'mimetype': 'image/png',
            'size': len(content),
            }
    person = Person()
    person.avatar = _to_fieldstorage(**data)

Note that the ``data`` dictionary described here has the same format as the deserialized value of a ``deform.widget.FileUploadWidget``.
See :class:`kotti.views.edit.content.FileAddForm` and :class:`kotti.views.edit.content.FileEditForm` for a full example of how to add or edit a model with a blob field.

Reading Blob Data
~~~~~~~~~~~~~~~~~

If you try directly to read data from an ``UploadedFileField`` you'll get a :class:`depot.fields.upload.UploadedFile` instance, which offers a dictionary-like interface to the stored file metadata and direct access to a stream with the stored file through the ``file`` attribute::

    person = DBSession.query(Person).get(1)
    blob = person.avatar.file.read()

You should never write to the file stream directly.
Instead, you should assign a new value to the ``UploadedFileField`` column, as described in the previous section.

Testing UploadedFileField Columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because :class:`depot.manager.DepotManager` acts as a singleton, special care needs to be taken when testing features that involve saving data into ``UploadedFileField`` columns.

``UploadedFileField`` columns require having at least one depot file storage configured.
You can use a fixture called ``filedepot`` to have a mock file storage available for your tests.

If you're developing new depot file storages you should use the ``no_filedepots`` fixture, which resets the configured depots for the test run and restores the default depots back, as a teardown.

Inheritance Issues with UploadedFileField Columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should be aware that, presently, subclassing a model with an ``UploadedFileField`` column doesn't work properly.
As a workaround, add a ``__declare_last__`` classmethod in your superclass model, similar to the one below, where we're fixing the ``data`` column of the ``File`` class. ::

    from depot.fields.sqlalchemy import _SQLAMutationTracker

    class File(Content):

        data = UploadedFileField()

        @classmethod
        def __declare_last__(cls):
            event.listen(cls.data, 'set', _SQLAMutationTracker._field_set, retval=True)


Migrating data between two different storages
---------------------------------------------

Kotti provides a script that can migrate blob data from one configured stored to another and update the saved fields with the new locations.
It is not needed to do this if you just want to add a new torage, or replace the default one, but you can use it if you'd like to consolidate the blob data in one place only.
You can invoke the script with::

    kotti-migrate-storage <config_uri> --from-storage <name> --to-storage <name>

The storage names are those assigned in the configuration file designated in ``<config_uri>``.
For example, let's assume you've started a website that has the default blob storage, the ``DBFileStorage`` named *dbfiles*.
You'd like to move all the existing blob data to a :class:`depot.io.local.LocalFileStorage` storage and make that the default.
First, add the ``LocalFileStorage`` depot, make it the default and place the old ``DBFileStorage`` in position *1*:::

    kotti.depot.0.backend = depot.io.local.LocalFileStorage
    kotti.depot.0.name = localfs
    kotti.depot.0.storage_path = /var/local/files
    kotti.depot.1.backend = kotti.filedepot.DBFileStorage
    kotti.depot.1.name = dbfiles

Now you can invoke the migration with:::

    kotti-migrate-storage <config_uri> --from-storage dbfiles --to-storage localfs

As always when dealing with migrations, make sure you backup your data first!


.. _Depot: https://depot.readthedocs.io/en/latest/

.. blobstorage:

BLOB-Storage
============

Kotti's default content types include :class:`kotti.resources.File` and :class:`koti.resources.Image` (which is directly derived from File).

By default the contents of a file is stored as a BLOB in the DB.
The benefit of that is having *all* content in a single place (the DB) which makes backups, exporting and importing of your site's data easy, as long as you don't have too many or too large files.
Downsides of this approach appear when your database server resides on a different host (network performance becomes a greater issue) or your DB dumps become too large to be handled efficiently.
These issues can be solved by chosing a different storage provider (available as an add-on), or implementing your own.

Using an existing storage provider
----------------------------------

To use an *external* storage provider, you usually need to add the add-on's ``kotti_configure`` to the list of configurators and specify the provider to be used (optionally with configuration options for that provider) via the ``kotti.blobstore`` setting in your ``*.ini`` file(s)::

  [app:main]
  use = egg:kotti
  kotti.configurators =
      kotti_filestore.kotti_configure
  kotti.blobstore = kotti_filestore.filestore://%(here)s/filestore
  ...

The value passed to the ``kotti.blobstore`` setting is an URL.
The scheme part (everything before ``://``) is the dotted path of the class which implements the provider.
The path is passed to the provider upon its initialization and is usually used to pass configuration options to the provider.
In the example above the path is the absolute path of the filesystem directory where ``kotti_blobstore`` should store the BLOBs.

Implementing your own storage provider
--------------------------------------

Implementing your own storage provider is pretty straight forward.
You just need to create a class that implements :class:`kotti.interfaces.IBlobStorage`.
See the interface's documentation for details.

Migration of existing data from one provider to another
-------------------------------------------------------

For your convenience Kotti provides a script to migrate your blobs from the DB storage to another provider or vice versa::

  # kotti-migrate-blobs development.ini --help
  Migrate BLOBs between the blobstore configured in the config file and the DB.

  Make sure you have a backup of your data and you know what you're doing.

  RUNNING THIS COMMAND WITH THE SAME OPTIONS TWICE IN A ROW WILL CAUSE PERMANENT
  LOSS OF DATA!

      Usage:
        kotti-migrate-blobs <config_uri> --from-db
        kotti-migrate-blobs <config_uri> --to-db

      Options:
        --from-db   Migrate FROM the DB TO the provider configured in your config
        --to-db     Migrate TO the DB FROM the provider configured in your config
        -h --help   Show this screen.

Existing storage provider add-ons
---------------------------------

  - `kotti_filestore`_

    Stores BLOBs on a filessystem on the host.
    Is fully transaction aware.

.. _kotti_filestore: https://pypi.python.org/pypi/kotti_filestore

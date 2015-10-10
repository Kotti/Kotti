.. _close-to-anonymous:

Close your site to anonymous users
==================================

This recipe describes how to configure Kotti to require users to log
in before they can view any of your site's pages.

To achieve this, we'll have to set our site's ACL.  A custom populator
will help us do that (see :ref:`kotti.populators`).

Remember that the default site ACL gives ``view`` privileges to every
user, including anonymous (see :ref:`develop-security`).  We'll thus
have to restrict the ``view`` permission to the ``viewer`` role:

.. code-block:: python

  from kotti.resources import get_root

  SITE_ACL = [
   (u'Allow', u'role:viewer', [u'view']),
   (u'Allow', u'role:editor', [u'view', u'add', u'edit']),
  ]

  def populate():
      site = get_root()
      site.__acl__ = SITE_ACL

.. _security:

Security
========

Kotti security is based on the concepts of users, groups, roles, permissions and workflow.

.. image:: /_static/user-group-role-permission.svg

User
    A user is an entity that can authenticate himself.

Group
    A group is a collection of users or other groups.

Permission
    A permission describes what is allowed on an object.

    Permissions are never directly assigned to users or groups but always
    aggregated in roles.

Role
    A Role is a collection of permissions.

    Users or groups can have global or local roles.

    Global Roles
        Global roles are assigned to a user or group via Kotti's user management
        screens.  They apply to every object in a site.  You should use them
        very rarely, maybe only assign the "Adminsitrator" role to the
        "Administrator" group.  This assignment is present by default in a fresh
        Kotti site.

    Local Roles
        Local roles are assigned to a user or group via the "Sharing" screen
        of a content object.  They apply only to this object and its children.

Workflow
    The workflow keeps track of the current state of each object lifecycle to manage content security.
    There is an initial state and you can move to other states thanks to transitions; each state defines a security matrix with roles and permissions.
    By default Kotti provides a two-state workflow (private and public) for all object types except files and images.
    Kotti's workflow implementation is based on `repoze.workflow`_.

How to create a new role
------------------------

Small recipe you can use if you want to create a new role:

.. code-block:: python

  from kotti.security import (
      Principal,
      ROLES,
      SHARING_ROLES,
      set_roles,
      set_sharing_roles,
      set_user_management_roles,
      )
  from kotti_yourpackage import _


  def add_role(role_id, role_title):
      """ Add role in share view and user management views """
      UPDATED_ROLES = ROLES.copy()
      UPDATED_ROLES[role_id] = Principal(role_id,
                                         title=role_title)
      UPDATED_SHARING_ROLES = list(SHARING_ROLES)
      UPDATED_SHARING_ROLES.append(role_id)
      set_roles(UPDATED_ROLES)
      set_sharing_roles(UPDATED_SHARING_ROLES)
      set_user_management_roles(UPDATED_SHARING_ROLES + ['role:admin'])


  add_role(u'role:customer', _(u'Customer'))

Practically you can add the code above to any file, as long as it is imported on application startup.
However, good practice would be to add it to your add on's ``__init__.py`` for small amounts of changes (like in the example) or to a separate file for larger amounts.

Workflows
---------

You can use an XML file (zcml) in order to describe your workflow.
You can see an example here: `workflow.zcml`_.

As you can see it is quite straightforward to add new states, transitions, permissions, etc.
You can easily turn the default 2-state website workflow into something completely different or turn your Kotti app into an intranet application.

The default workflow definition is loaded from your project's ``.ini`` file  (using the ``kotti.use_workflow`` setting).
The ``kotti.use_workflow`` setting's default value is:

.. code-block:: ini

    kotti.use_workflow = kotti:workflow.zcml

You can change change the default workflow for your site, register new workflows related to specific content types or disable it completely.

How to disable the default workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Kotti is shipped with a simple workflow definition based on private and public states.
If your particular use case does not require workflows at all, you can disable this feature with a non true value. For example:

.. code-block:: ini

    kotti.use_workflow = 0

How to override the default workflow for all content types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default workflow is quite useful for websites, but sometimes you need something different.
Just point the ``kotti.use_workflow`` setting to your zcml file:

.. code-block:: ini

    kotti.use_workflow = kotti_yourplugin:workflow.zcml

The simplest way to deal with workflow definitions is:

1. create a copy of the default workflow definition and
2. customize it (change permissions, add new states, permissions, transitions, initial state and so on).

If you change workflow settings, you need to reset all your content's workflow states and thus the permissions for all objects under workflow control using the ``kotti-reset-workflow`` console script.

kotti-reset-workflow command usage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you change workflow settings you'll need to update security.

.. code-block:: bash

    $ kotti-reset-workflow --help
    Reset the workflow of all content objects in the database.

        This is useful when you want to migrate an existing database to
        use a different workflow.  When run, this script will reset all
        your content objects to use the new workflow, while trying to
        preserve workflow state information.

        For this command to work, all currently persisted states must map
        directly to a state in the new workflow.  As an example, if
        there's a 'public' object in the database, the new workflow must
        define 'public' also.

        If this is not the case, you may choose to reset all your content
        objects to the new workflow's *initial state* by passing the
        '--purge-existing' option.

        Usage:
          kotti-reset-workflow <config_uri> [--purge-existing]

        Options:
          -h --help          Show this screen.
          --purge-existing   Reset all objects to new workflow's initial state.

How to enable the standard workflow for images and files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Images and files are not associated with the default workflow.
If you need a workflow for these items you need to attach the ``IDefaultWorkflow`` marker interface.

You can add the following lines in your includeme function:

.. code-block:: python

    from zope.interface import implementer
    from kotti.interfaces import IDefaultWorkflow
    from kotti.resources import File
    from kotti.resources import Image
    ...

    def includeme(config):
        ...
        # enable workflow for images and files
        implementer(IDefaultWorkflow)(Image)
        implementer(IDefaultWorkflow)(File)
        ...

How to assign a different workflow to a content type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We are going to use the default workflow for standard content types and a custom workflow for content types providing the ``ICustomContent`` marker interface.
All other content types will still use the default workflow.
Third party developers will be able to override our custom workflow without having to touch any line of code (just a ``.ini`` configuration file)

Let's assume you are starting with a standard Kotti package created with ``pcreate -s kotti kotti_wf``.

Four steps are needed:

1. create a new marker interface ICustomContent,
2. change ``kotti_wf.resource`` (replace ``IDefaultWorkflow`` with our new ``ICustomContent``),
3. create the new workflow definition and
4. register your workflow definition.

Create a new module ``kotti_wf/interfaces.py`` with this code.
This is **optional** but it doesn't hurt, the important thing is to omit the ``IDefaultWorkflow`` implementer from ``kotti_wf.resources``:

.. code-block:: python

    from zope.interface import Interface


    class ICustomContent(Interface):
        """ Custom content marker interface """

Change your ``kotti_wf.resources`` module like so:

.. code-block:: python

    from kotti.resources import Content
    from zope.interface import implements

    from kotti_wf.interfaces import ICustomContent


    class CustomContent(Content):
        """ A custom content type. """

        implements(ICustomContent)

Here it is, our "custom" workflow definition assigned to our ``ICustomContent`` marker interface:

.. code-block:: xml

    <configure xmlns="http://namespaces.repoze.org/bfg"
               xmlns:i18n="http://xml.zope.org/namespaces/i18n"
               i18n:domain="Kotti">

      <include package="repoze.workflow" file="meta.zcml"/>

      <workflow
          type="security"
          name="custom"
          state_attr="state"
          initial_state="private"
          content_types="kotti_wf.interfaces.ICustomContent"
          permission_checker="pyramid.security.has_permission"
          >

        <state name="private" callback="kotti.workflow.workflow_callback">

          <key name="title" value="_(u'Private')" />
          <key name="order" value="1" />

          <key name="inherit" value="0" />
          <key name="system.Everyone" value="" />
          <key name="role:viewer" value="view" />
          <key name="role:editor" value="view add edit delete state_change" />
          <key name="role:owner" value="view add edit delete manage state_change" />

        </state>

      </workflow>

    </configure>

Last you have to tell Kotti to register your new custom workflow including our ``zcml`` file:

.. code-block:: ini

    kotti.zcml_includes = kotti_wf:workflow.zcml

Special cases:

* if you change workflow settings on a site with existing ``CustomContent`` instances, you need to update the workflow settings using the ``kotti-reset-workflow`` command.

* if you assign a new workflow definition to a content that already provides the ``IDefaultWorkflow`` marker interface (by default all content types except files and images), you will have to create and attach on your workflow definition an ``elector`` function (it is just a function accepting a context and returning ``True`` or ``False``)

.. _repoze.workflow: http://docs.repoze.org/workflow/
.. _workflow.zcml: https://github.com/Kotti/Kotti/blob/master/kotti/workflow.zcml.

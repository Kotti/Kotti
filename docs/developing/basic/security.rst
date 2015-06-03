.. _security:

Security
========

Kotti security is based on the concepts of users, groups, roles and permissions.

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

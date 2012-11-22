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

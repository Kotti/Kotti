.. _add-to-edit-interface:

Adding links and actions to the edit interface
==============================================

This document covers how to customize the available links and actions of the edit interface (the extra tabs and menus that appear after you log in).

The basic building block is the link, ``kotti.util.Link``. Instantiate it as:

.. code-block:: python

    link = Link('name', _(u'Title'))

The name refers to a view name available on the context.

There's also:

    * ``kotti.util.LinkParent``, which allows grouping of links
    * ``kotti.util.LinkRenderer``, which, instead of generating a simple link, allows you to customize how it's rendered (you can insert anything there, even another submenu based on a ``LinkParent``).
    * ``kotti.util.ActionButton``, very similar to a simple link, but generates a button instead.

Adding a new option to the Administration menu
----------------------------------------------

Adding a new link as an option in the **Administration** menu, in the *Site Setup* section is easy. In your ``kotti_configure`` function, add:

.. code-block:: python

    from kotti.util import Link
    from kotti.views.site_setup import CONTROL_PANEL_LINKS

    def kotti_configure(settings):
        link = Link('name', _(u'Title'))
        CONTROL_PANEL_LINKS.append(link)

Make a new section in the actions menu
--------------------------------------
The *Set default view* section looks really nice. To add your own separated section in the **Action** menu and make that available to all content types:

.. code-block:: python

    from kotti.util import LinkRenderer
    from kotti.resources import default_actions

    def kotti_configure(settings):
        default_actions.append(LinkRenderer("my-custom-submenu"))

So far we've added a ``LinkRenderer`` to the ``default_actions`` which are used by all content inheriting ``Content``. This LinkRenderer will render a view and insert its result in the menu.

.. code-block:: python

    @view_config(
        name="my-custom-submenu", permission="edit",
        renderer="mypackage:templates/edit/my-custom-submenu.pt")
    def my_custom_submenu(context, request):
        return {}

And the template:

.. code-block:: html

    <tal:menu i18n:domain="mypackage">
        <li class="divider"></li>
        <li role="presentation" class="dropdown-header" i18n:translate="">
            My own actions
        </li>
        <li>
            <a i18n:translate="" href="${request.resource_url(context, 'someview')}">
                View title here
            </a>
        </li>
    </tal:menu

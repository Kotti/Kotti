.. _tut-2:

Tutorial Part 2: A Content Type
===============================

Kotti's default content types include ``Document``, ``Image`` and ``File``.
In this part of the tutorial, we'll add to these built-in content types by making a ``Poll`` content type which will allow visitors to view polls and vote on them.

Adding Models
-------------

When creating our add-on, the scaffolding added the file ``kotti_mysite/kotti_mysite/resources.py``.
If you open ``resources.py`` you'll see that it already contains code for a sample content type ``CustomContent`` along with the following imports that we will use.

.. code-block:: python

  from kotti.resources import Content
  from sqlalchemy import Column
  from sqlalchemy import ForeignKey
  from sqlalchemy import Integer

Add the following definition for the ``Poll`` content type to ``resources.py``.

.. code-block:: python

  class Poll(Content):
      id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)

      type_info = Content.type_info.copy(
          name=u'Poll',
          title=u'Poll',
          add_view=u'add_poll',
          addable_to=[u'Document'],
      )

Things to note here:

- Kotti's content types use SQLAlchemy_ for definition of persistence.

- ``Poll`` derives from :class:`kotti.resources.Content`, which is the common base class for all content types.

- ``Poll`` declares a :class:`sqlalchemy.Column <sqlalchemy.schema>` ``id``, which is required to hook it up with SQLAlchemy's inheritance.

- The ``type_info`` class attribute does essential configuration.
  We refer to name and title, two properties already defined as part of ``Content``, our base class.
  The ``add_view`` defines the name of the add view, which we'll come to in a second.
  Finally, ``addable_to`` defines which content types we can add ``Poll`` items to.

- We do not need to define any additional :class:`sqlalchemy.Column <sqlalchemy.schema>` properties, as the ``title``
  is the only property we need for this content type.

We'll add another content class to hold the choices for the poll.
Add this into the same ``resources.py`` file:

.. code-block:: python

  class Choice(Content):
      id = Column(Integer(), ForeignKey('contents.id'), primary_key=True)
      votes = Column(Integer())

      type_info = Content.type_info.copy(
          name=u'Choice',
          title=u'Choice',
          add_view=u'add_choice',
          addable_to=[u'Poll'],
      )

      def __init__(self, votes=0, **kwargs):
          super(Choice, self).__init__(**kwargs)
          self.votes = votes

The ``Choice`` class looks very similar to ``Poll``.
Notable differences are:

- It has an additional sqla.Column property called ``votes``.
  We'll use this to store how many votes were given for the particular choice.
  We'll again use the inherited ``title`` column to store the title of our choice.

- The ``type_info`` defines the title, the ``add_view`` view, and that choices may only be added *into* ``Poll`` items, with the line ``addable_to=[u'Poll']``.

.. _adding-forms-and-a-view:

Adding Forms and a View
-----------------------

Views (including forms) are typically put into a module called ``views``.
The Kotti scaffolding further separates this into ``view`` and ``edit`` files inside a ``views`` directory.

Open the file at ``kotti_mysite/kotti_mysite/views/edit.py``.
It already contains code for the ``CustomContent`` sample content type.
We will take advantage of the imports already there.

.. code-block:: python

  import colander
  from kotti.views.edit import ContentSchema
  from kotti.views.form import AddFormView
  from kotti.views.form import EditFormView
  from pyramid.view import view_config

  from kotti_mysite import _

Some things to note:

- Colander_ is the library that we use to define our schemas.
  Colander allows us to validate schemas against form data.

- Our class inherits from :class:`kotti.views.edit.ContentSchema` which itself inherits from :class:`colander.MappingSchema`.

- ``_`` is how we hook into i18n for translations.

Add the following code to ``views/edit.py``:

.. code-block:: python

  class PollSchema(ContentSchema):
      """Schema for Poll"""

      title = colander.SchemaNode(
          colander.String(),
          title=_(u'Question'),
      )


  class ChoiceSchema(ContentSchema):
      """Schema for Choice"""

      title = colander.SchemaNode(
          colander.String(),
          title=_(u'Choice'),
      )

The two classes define the schemas for our forms.
The schemas specify which fields we want to display in the forms.
We want to display the ``title`` field.

Let's move on to building the actual forms.
Add this to ``views/edit.py``:

.. code-block:: python

  from kotti_mysite.resources import Choice
  from kotti_mysite.resources import Poll


  @view_config(name='edit', context=Poll, permission='edit',
               renderer='kotti:templates/edit/node.pt')
  class PollEditForm(EditFormView):
      schema_factory = PollSchema


  @view_config(name=Poll.type_info.add_view, permission='add',
               renderer='kotti:templates/edit/node.pt')
  class PollAddForm(AddFormView):
      schema_factory = PollSchema
      add = Poll
      item_type = u"Poll"


  @view_config(name='edit', context=Choice, permission='edit',
               renderer='kotti:templates/edit/node.pt')
  class ChoiceEditForm(EditFormView):
      schema_factory = ChoiceSchema


  @view_config(name=Choice.type_info.add_view, permission='add',
               renderer='kotti:templates/edit/node.pt')
  class ChoiceAddForm(AddFormView):
      schema_factory = ChoiceSchema
      add = Choice
      item_type = u"Choice"

Using the ``AddFormView`` and ``EditFormView`` base classes from Kotti, these forms are simple to define.
We associate the schemas defined above, setting them as the ``schema_factory`` for each form, and we specify the content types to be added by each.

We use ``@view_config`` to add our views to the application.
This takes advantage of a ``config.scan()`` call in ``__init__.py`` discussed below.
Notice that we can declare ``permission``, ``context``, and a ``template`` for each form, along with its ``name``.

Wiring up the Content Types and Forms
-------------------------------------

Before we can see things in action, we need to add a reference to our new content types in ``kotti_mysite/kotti_mysite/__init__.py``.

Open ``__init__.py`` and modify the ``kotti_configure`` method so that the
``settings['kotti.available_types']`` line looks like this.

.. code-block:: python
  :emphasize-lines: 4-6

    def kotti_configure(settings):
          ...
        settings['pyramid.includes'] += ' kotti_mysite'
        settings['kotti.available_types'] += (
            ' kotti_mysite.resources.Poll' +
            ' kotti_mysite.resources.Choice')
        settings['kotti.fanstatic.view_needed'] += (
            ' kotti_mysite.fanstatic.css_and_js')
        ...

Here, we've added our two content types to the site's ``available_types``, a global
registry.
We also removed the ``CustomContent`` content type included with the scaffolding.

Notice the ``includeme`` method at the bottom of ``__init__.py``.
It includes the call to ``config.scan()`` that we mentioned above while discussing the ``@view_config`` statements in our views.

.. code-block:: python

  def includeme(config):
      ...
      config.scan(__name__)

You can see the Pyramid documentation for scan_ for more information.

Adding a Poll and Choices to the site
-------------------------------------

Let's try adding a Poll and some choices to the site.
Start the site up with the command

.. code-block:: bash

  bin/pserve app.ini

Login with the username *admin* and password *qwerty* and click on the Add menu button.
You should see a few choices, namely the base Kotti classes ``Document``, ``File`` and ``Image`` and the Content Type we added, ``Poll``.

Lets go ahead and click on ``Poll``.
For the question, let's write *"What is your favourite color?"*.
Now let's add three choices, *"Red"*, *"Green"* and *"Blue"* in the same way we added the poll.
Remember that you must be in the context of the poll to add each choice.

If we now go to the poll we added, we can see the question, but not our choices, which is definitely not what we wanted.
Let us fix this, shall we?

Adding a custom View to the Poll
--------------------------------

First, we need to write a view that will send the needed data (in our case, the choices we added to our poll).
Here is the code, added to ``view.py``.

.. code-block:: python

  from kotti_mysite.fanstatic import css_and_js
  from kotti_mysite.resources import Poll


  @view_defaults(context=Poll)
  class PollViews(BaseView):
      """ Views for :class:`kotti_mysite.resources.Poll` """

      @view_config(name='view', permission='view',
                   renderer='kotti_mysite:templates/poll.pt')
      def poll_view(self):
          css_and_js.need()
          choices = self.context.children
          return {
              'choices': choices,
          }

Since we want to show all ``Choices`` added to a ``Poll`` we can simply use the ``children`` attribute. This will return a list of all the 'children' of a ``Poll`` which are exactly the ``Choices`` added to that particular ``Poll``.
The view returns a dictionary of all choices under the keyword *'choices'*.
The keywords a view returns are automatically available in it's template.

Next on, we need a template to actually show our data.
It could look something like this.
Create a folder named ``templates`` and put the file ``poll.pt`` into it.

.. code-block:: html

  <!DOCTYPE html>
  <html xmlns:tal="http://xml.zope.org/namespaces/tal"
        xmlns:metal="http://xml.zope.org/namespaces/metal"
        metal:use-macro="api.macro('kotti:templates/view/master.pt')">

    <article metal:fill-slot="content" class="poll-view content">
      <h1>${context.title}</h1>
      <ul>
          <li tal:repeat="choice choices">${choice.title}</li>
      </ul>
    </article>

  </html>

The first 6 lines are needed so our template plays nicely with the master template (so we keep the add/edit bar, base site structure etc.).
The next line prints out the context.title (our question) inside the ``<h1>`` tag and then prints all choices (with links to the choice) as an unordered list.

.. note::

  We are using two 'magically available' attributes in the template - ``context`` and ``choices``.

  - ``context`` is automatically available in all templates and as the name implies it is the context of the view (in this case the ``Poll`` we are currently viewing).

  - ``choices`` is available because we sent it to the template in the Python part of the view.
    You can of course send multiple variables to the template, you just need to return them in your Python code.

With this, we are done with the second tutorial.
Restart the application, take a look at the new ``Poll`` view and play around with the template until you are completely satisfied with how our data is presented.

.. note::

  If you will work with templates for a while (or any time you're developing basically) using the pyramid *'reload_templates'* and *'debug_templates'* options is recommended, as they allow you to see changes to the template without having to restart the application.
  These options need to be put in your configuration INI under the *'[app:kotti]'* section.

  .. code-block:: ini

    [app:kotti]
    pyramid.reload_templates = true
    pyramid.debug_templates = true

In the :ref:`next tutorial <tut-3>`, we will learn how to enable our users to actually vote for one of the ``Poll`` options.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Colander: https://colander.readthedocs.io/
.. _scan: http://docs.pylonsproject.org/docs/pyramid/en/latest/api/config.html#pyramid.config.Configurator.scan

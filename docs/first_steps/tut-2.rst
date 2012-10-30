.. _tut-2:

Tutorial Part 2: A Content Type
===============================

Kotti's default content types include ``Document``, ``Image`` and ``File``.  In
this part of the tutorial, we'll add add to these built-in content types by
making a ``Poll`` content type which will allow visitors to view polls and vote
on them.

Adding Models
-------------

Let's create a new file at ``kotti_mysite/kotti_mysite/resources.py``
and add the definition of the ``Poll`` content type:

.. code-block:: python

  import sqlalchemy as sqla

  from kotti.resources import Content


  class Poll(Content):
      id = sqla.Column(
          sqla.Integer(), sqla.ForeignKey('contents.id'), primary_key=True)

      type_info = Content.type_info.copy(
          name=u'Poll',
          title=u'Poll',
          add_view=u'add_poll',
          addable_to=[u'Document'],
          )

Things to note here:

- Kotti's content types use SQLAlchemy_ for definition of persistence.

- ``Poll`` derives from :class:`kotti.resources.Content`, which is the
  common base class for all content types.

- ``Poll`` declares a sqla.Column ``id``, which is required to hook
  it up with SQLAlchemy's inheritance. 
  
- The type_info class attribute does essential configuration. We
  refer to name and title, two properties already defined as part of
  ``Content``, our base class.  The ``add_view`` defines the name of the add
  view, which we'll come to in a second.  Finally, ``addable_to`` defines which
  content types we can add ``Poll`` items to.

- We do not need to define any additional sqlaColumn() properties, as the title
  is the only property we need for this content type.

We'll add another content class to hold the choices for the poll.  Add
this into the same ``resources.py`` file:

.. code-block:: python

  class Choice(Content):
      id = sqla.Column(
          sqla.Integer(), sqla.ForeignKey('contents.id'), primary_key=True)
      votes = sqla.Column(sqla.Integer())

      type_info = Content.type_info.copy(
          name=u'Choice',
          title=u'Choice',
          add_view=u'add_choice',
          addable_to=[u'Poll'],
          )

      def __init__(self, votes=0, **kwargs):
          super(Choice, self).__init__(**kwargs)
          self.votes = votes

The ``Choice`` class looks very similar to ``Poll``.  Notable
differences are:

- It has an additional sqla.Column property called ``votes``.  We'll use this
  to store how many votes were given for the particular choice.  We'll again
  use the inherited ``title`` column to store the title of our choice.

- The ``type_info`` defines the title, the ``add_view`` view, and that
  choices may only be added *into* ``Poll`` items, with the line
  ``addable_to=[u'Poll']``.

Adding Forms and a View
-----------------------

Views (including forms) are typically put into a module called
``views``.  Let's create a new file for this module at
``kotti_mysite/kotti_mysite/views.py`` and add the following code:

.. code-block:: python

  import colander

  class PollSchema(colander.MappingSchema):
      title = colander.SchemaNode(
          colander.String(),
          title=u'Question',
          )

  class ChoiceSchema(colander.MappingSchema):
      title = colander.SchemaNode(
          colander.String(),
          title=u'Choice',
          )

Colander_ is the library that we use to define our schemas.  Colander
allows us to validate schemas against form data.

The two classes define the schemas for our add and edit forms.  That
is, they specify which fields we want to display in the forms.

Let's move on to building the actual forms.  Add this to ``views.py``:

.. code-block:: python

  from kotti.views.form import AddFormView
  from kotti.views.form import EditFormView

  from .resources import Choice
  from .resources import Poll

  class PollEditForm(EditFormView):
      schema_factory = PollSchema

  class PollAddForm(AddFormView):
      schema_factory = PollSchema
      add = Poll
      item_type = u"Poll"

  class ChoiceEditForm(EditFormView):
      schema_factory = ChoiceSchema

  class ChoiceAddForm(AddFormView):
      schema_factory = ChoiceSchema
      add = Choice
      item_type = u"Choice"
 

Using the ``AddFormView`` and ``EditFormView`` base classes from
Kotti, these forms are simple to define. We associate the schemas
defined above, setting them as the schema_factory for each form,
and we specify the content types to be added by each.

Wiring up the Content Types and Forms
-------------------------------------

It's time for us to see things in action. For that, some configuration
of the types and forms is in order.

Find ``kotti_mysite/kotti_mysite/__init__.py`` and add configuration that
registers our new code in the Kotti site.

We change the ``kotti_configure`` function to look like:

.. code-block:: python

 def kotti_configure(settings):
     settings['kotti.fanstatic.view_needed'] += (
         ' kotti_mysite.static.kotti_mysite_group')
     settings['kotti.available_types'] += (
         ' kotti_mysite.resources.Poll kotti_mysite.resources.Choice')
     settings['pyramid.includes'] += ' kotti_mysite'

Here, we've added our two content types to the site's available_types, a glogal
registry.

Now add a function called ``includeme`` to the same file:

.. code-block:: python

  def includeme(config):
      from .resources import Poll
      from .resources import Choice
      from .views import PollAddForm
      from .views import PollEditForm
      from .views import ChoiceAddForm
      from .views import ChoiceEditForm

      config.add_view(
          PollAddForm,
          name='add_poll',
          permission='add',
          renderer='kotti:templates/edit/node.pt',
          )
      config.add_view(
          PollEditForm,
          context=Poll,
          name='edit',
          permission='edit',
          renderer='kotti:templates/edit/node.pt',
          )
      config.add_view(
          ChoiceAddForm,
          name='add_choice',
          permission='add',
          renderer='kotti:templates/edit/node.pt',
          )
      config.add_view(
          ChoiceEditForm,
          context=Choice,
          name='edit',
          permission='edit',
          renderer='kotti:templates/edit/node.pt',
          )

Here, we call ``config.add_view`` once for each form. The first argument
of each call is the form class. The second argument gives the name of the
view. The names of each add view, `add_poll` and `add_choice`, match the
names set in the type_info class attribute of the types (Compare to the
classes where Poll() and Choice() are defined). The names of the edit views
are simply `edit`, 


.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Colander: http://colander.readthedocs.org/

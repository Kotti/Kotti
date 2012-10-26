.. _tut-2:

Tutorial part 2: A content type
===============================

Kotti's default content types include ``Document``, ``Image`` and
``File``.  In this part of the tutorial, we'll add a ``Poll`` content
type which will allow visitors to view polls and vote on them.

Adding models
-------------

Let's create a new file at ``kotti_mysite/kotti_mysite/resources.py``
and put the definition of the ``Poll`` content type therein:

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

- Kotti's content types use SQLAlchemy_ for persistence

- ``Poll`` derives from :class:`kotti.resources.Content`, which is the
  common base class for all content types.

- ``Poll`` declares a single columns ``id``, which is required to hook
  it up with SQLAlchemy's inheritance.  We don't define any additional
  columns since all we need is a title, and that's already defined as
  part of ``Content``, our base class.

- The ``type_info`` class attribute defines the ``title`` of a poll as
  it'll be used in the user interface.  The ``add_view`` defines the
  name of the add view, which we'll come to in a second.  Finally,
  ``addable_to`` defines which content types we can add ``Poll`` items
  to.

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

- It has an additional column called ``votes``.  We'll use this to
  store how many votes were given for the particular choice.  We'll
  again use the inherited ``title`` column to store the title of our
  choice.


- It has different columns, namely ``choice`` and ``votes`` are
  different.

- The ``type_info`` defines a different title and ``add_view``.  It
  also defines that choices may only be added *into* ``Poll`` items
  through ``addable_to=[u'Poll']``.

Adding forms and a view
-----------------------

Views (including forms) are typically put into a module called
``views``.  Let's create a new file at
``kotti_mysite/kotti_mysite/views.py`` and put inside the following:

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

These two classes define the schema for our add and edit forms.  That
is, they represent which fields we want to display in the form.

Colander_ is the library that we use to define our schemas.  Colander
allows us to validate schemas against form data.

Let's move on to building our actual forms.  Add this to ``views.py``:

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
Kotti, these forms become pretty simple.

Wiring up the content types and forms
-------------------------------------

It's time for us to see things in action.  Let's configure our content
types and forms, so that we can see things in action.

Let's go back to ``kotti_mysite/kotti_mysite/__init__.py`` and add a
little more configuration to register our new code so that it can be
used in our Kotti site.

We change the ``kotti_configure`` function to look like so:

.. code-block:: python

 def kotti_configure(settings):
     settings['kotti.fanstatic.view_needed'] += (
         ' kotti_mysite.static.kotti_mysite_group')
     settings['kotti.available_types'] += (
         ' kotti_mysite.resources.Poll kotti_mysite.resources.Choice')
     settings['pyramid.includes'] += ' kotti_mysite'

Now we'll add another function in the same file called ``includeme``:

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

Here, we call ``config.add_view`` once for each form.  XXX


.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Colander: http://colander.readthedocs.org/

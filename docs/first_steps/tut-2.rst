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

  from kotti_mysite.resources import Choice
  from kotti_mysite.resources import Poll

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
          ' kotti_mysite.fanstatic.kotti_mysite_group')
      settings['kotti.available_types'] += (
          ' kotti_mysite.resources.Poll kotti_mysite.resources.Choice')
      settings['pyramid.includes'] += ' kotti_mysite'

Here, we've added our two content types to the site's available_types, a global
registry.

Now add a function called ``includeme`` to the same file:

.. code-block:: python

  def includeme(config):
      from kotti_mysite.resources import Poll
      from kotti_mysite.resources import Choice
      from kotti_mysite.views import PollAddForm
      from kotti_mysite.views import PollEditForm
      from kotti_mysite.views import ChoiceAddForm
      from kotti_mysite.views import ChoiceEditForm

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
are simply `edit`, the names of add views are simply `add`. We can, of course,
add our own view names, but `add` and `edit` should be used for adding and
editing respectively, as Kotti uses those names for its base functionality.

Adding a Poll and Choices to the site
-------------------------------------

Let's try adding a Poll and some choices to the site. Start the site up with
the command

.. code-block:: bash

  bin/pserve app.ini

Login with the username *admin* and password *qwerty* and click on the Add menu
button. You should see a few choices, namely the base Kotti classes
``Document``, ``File`` and ``Image`` and the Content Type we added, ``Poll``.

Lets go ahead and click on ``Poll``. For the question, let's write
*What is your favourite color?*. Now let's add three choices,
*Red*, *Green* and *Blue* in the same way we added the poll.

If we now go to the poll we added, we can see the question, but not our choices,
which is definitely not what we wanted. Let us fix this, shall we?

Adding a custom View to the Poll
--------------------------------

Since there are plenty tutorials on how to write TAL templates, we will not
write a complete one here, but just a basic one, to show off the general idea.

First, we need to write a view that will send the needed data (in our case,
the choices we added to our poll). Here is the code, added to ``view.py``.

.. code-block:: python

  from kotti import DBSession
  from kotti_mysite.fanstatic import kotti_mysite_group


  def poll_view(context, request):
      kotti_mysite_group.need()
      choices = DBSession().query(Choice).all()
      choices = [choice for choice in choices if choice.parent.id == context.id]
      return {
          'choices': choices
      }

As you can see, we simply queried the database for all choices, then went
through them and selected only the ones that were added to the poll we are
currently viewing. We do this by comparing the *context.id* with the
*choice.parent.id*. If they are the same, this particular choice was added
to the ``Poll`` we are currently viewing.
Finally, we return a dictionary of all choices under the keyword *choices*.

Next on, we need a template to actually show our data. It could look something
like this. The file is ``poll.pt`` and goes under the ``templates`` folder.

.. code-block:: html

  <!DOCTYPE html>
  <html xmlns:tal="http://xml.zope.org/namespaces/tal"
        xmlns:metal="http://xml.zope.org/namespaces/metal"
        metal:use-macro="api.macro('kotti:templates/view/master.pt')">

    <article metal:fill-slot="content" class="poll-view content">
      <h1>${context.title}</h1>
      <ul>
          <li tal:repeat="choice choices">
            <a href="${request.resource_url(choice)}">${choice.title}</a>
          </li>
      </ul>
    </article>

  </html>

The first 6 lines are needed so our template plays nicely with the master
template (so we keep the add/edit bar, base site structure etc.).
The next line prints out the context.title (our question) inside the <h1> tag
and then prints all choices (with links to the choice) as an unordered list.

Now all that remains is linking the two together. We do this in the
``__init__.py`` file, like this.

.. code-block:: python

  from kotti_mysite.views import poll_view

  config.add_view(
      poll_view,
      context=Poll,
      name='view',
      permission='view',
      renderer='kotti_mysite:templates/poll.pt',
  )

With this, we are done with the second tutorial. Restart the server instance,
take a look at the new ``Poll`` view and play around with the template until
you are completely satisfied with how our data is presented.

In the next tutorial, we will learn how to enable our users to actually vote
for one of the ``Poll`` options.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Colander: http://colander.readthedocs.org/

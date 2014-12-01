.. _tut-3:

Tutorial Part 3: User interaction
=================================

In this part of the tutorial, we will change the site we made in the previous one so our users can actually vote on our polls.

Enabling voting on Poll Choices
-------------------------------

We will enable users to vote using a new view.
When the user goes to that link, his or her vote will be saved and they will be redirected back to the Poll.

First, let's construct a new view, this time inside ``kotti_mysite/kotti_mysite/views/view.py``.
Add the following code to ``views/view.py``.

.. code-block:: python

  @view_defaults(context=Choice)
  class ChoiceViews(BaseView):
      """ Views for :class:`kotti_mysite.resources.Choice` """

      @view_config(name='vote', permission='edit')
      def vote_view(self):
          self.context.votes += 1
          return HTTPFound(location=self.request.resource_url(self.context.parent))

The view will be called on the Choice content type, so the context is the Choice itself.
We add 1 to the current votes of the Choice, then we do a redirect using :class:`pyramid.httpexceptions.HTTPFound`.
The location is the parent of our context - the Poll in which our Choice resides.

With this, we can now vote on a Choice by appending /vote at the end of the Choice URL.

Changing the Poll view so we see the votes
------------------------------------------

First, we will add some extra content into our poll_view so we are able to show current votes of a Choice.

.. code-block:: python
  :emphasize-lines: 4,7

  def poll_view(self):
      css_and_js.need()
      choices = self.context.values()
      all_votes = sum(choice.votes for choice in choices)
      return {
          'choices': choices,
          'all_votes': all_votes
      }

Our view will now be able to get the sum of all votes in the poll via the *all_votes* variable.
We will also want to change the link to go to our new vote view.
Open ``poll.pt`` and change the link into

.. code-block:: html
  :emphasize-lines: 3-5

  ...
  <li tal:repeat="choice choices">
    <a href="${request.resource_url(choice)}/vote">
      ${choice.title}
    </a> (${choice.votes}/${all_votes})
  </li>
  ...

This will add the number of votes/all_votes after each choice and enable us to vote by clicking on the Choice.
Fire up the server and go test it now.

Adding an info block about voting on the view
---------------------------------------------

As you can see, the voting now works, but it doesn't look particulary good.
Let us at least add a nice information bubble when we vote alright?
The easiest way to go about that is to use ``request.session.flash``, which allows us to flash different messages (success, error, info etc.).
Change the ``vote_view`` to include the the flash message before redirecting.

.. code-block:: python
  :emphasize-lines: 3-5

  def vote_view(self):
      self.context.votes += 1
      self.request.session.flash(
          u'You have just voted for the choice "{0}"'.format(
              self.context.title), 'info')
      return HTTPFound(
          location=self.request.resource_url(self.context.parent))


As before, I encourage you to play around a bit more, as you learn much by trying our new things.
A few ideas on what you could work on are:

- Change the Choice content type so it has an extra description field that is not required (if you change database content, you will need to delete the database or do a migration).
  Then make a new Choice view that will list the extra information.
- Make sure only authenticated users can vote, anonymous users should see the results but when trying to vote, it should move them to the login page.
  Also make sure that each user can vote only once, and list all users who voted for the Choice on the Choice's view.


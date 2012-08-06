from kotti import get_settings
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.security import get_principals
from kotti.security import SITE_ACL
from kotti.workflow import get_workflow


def populate_users():
    principals = get_principals()
    if u'admin' not in principals:
        principals[u'admin'] = {
            'name': u'admin',
            'password': get_settings()['kotti.secret'],
            'title': u"Administrator",
            'groups': [u'role:admin'],
            }


def populate():
    if DBSession.query(Node).count() == 0:
        root = Document(**_ROOT_ATTRS)
        root.__acl__ = SITE_ACL
        DBSession.add(root)
        root['about'] = Document(**_ABOUT_ATTRS)

        wf = get_workflow(root)
        if wf is not None:
            DBSession.flush()  # Initializes workflow
            wf.transition_to_state(root, None, u'public')

    populate_users()

_ROOT_ATTRS = dict(
    name=u'',  # (at the time of writing) root must have empty name!
    title=u'Welcome to Kotti',
    description=u'Congratulations! You have successfully installed Kotti.',
    body=u"""
<h2>Log in</h2>

<p>
  You can <a href="/edit" class="btn btn-success">log in</a> to your
  site and start changing its contents.  If you haven't chosen a
  password for you admin account yet, it'll likely be <i>qwerty</i>.
</p>

<p>
  Once you're logged in, you'll see the black editor bar on the top
  of the page.  It will allow you to switch between editing and
  viewing the current page as it will appear to your visitors.
</p>

<h2>Configure</h2>
<p>
  Find out how to configure your Kotti's title and many other settings
  using a simple text file in your file system.
</p>
<p>
  <a href="http://kotti.readthedocs.org/en/latest/configuration.html"
     class="btn btn-info">Configuration manual</a>
</p>
<p>
  A number of add-ons allow you to extend the functionality of your
  Kotti site.
</p>
<p>
  <a href="http://pypi.python.org/pypi?%3Aaction=search&term=kotti"
     class="btn btn-info">Kotti add-ons</a>
</p>

<h2>Develop</h2>
<p>
  Kotti aims to be easy and extensible.  Check out the developer manual.
</p>
<p>
  <a href="http://kotti.readthedocs.org/en/latest/developer-manual.html"
     class="btn btn-info">Developer Manual</a>
</p>

<h2>Documentation</h2>
<p>
  Wonder what more you can do with Kotti?  What license it has?  Read
  the manual for more information.
</p>
<p>
  <a href="http://kotti.readthedocs.org/en/latest/"
     class="btn btn-info">Documentation</a>
</p>
""")

_ABOUT_ATTRS = dict(
    title=u'About',
    description=u'Our company is the leading manufacturer of foo widgets used in a wide variety of aviation and and industrial products.',
    body=u"""
<p>
  <img alt="five colorful Extra EA300 airplanes flying in formation"
   src="http://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Northern_Lights_Formation.jpg/640px-Northern_Lights_Formation.jpg"
   width="640" height="376" />
</p>

<p>
   Our worldwide headquarters:
</p>

<address>
  Foo World<br />
  123 Nowhere Street, Suite 777<br />
  Omak, WA   98841   USA<br />
  +1-509-555-0100<br />
  widgets@foowrld.example.com
</address>

<p><small style="font-size: smaller">
  <em>Photo credit:</em> "Northern Lights Formation" by FlugKerl2.
  <a href="http://commons.wikimedia.org/wiki/File:Northern_Lights_Formation.jpg">
  Copyright info</a>.
  Originally published in the
  <a href="http://en.wikipedia.org/wiki/Extra_EA-300"> Extra EA-300</a>
  article.
</small></p>
""")

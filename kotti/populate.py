"""
Populate contains two functions that are called on application startup
(if you haven't modified kotti.populators).
"""

from pyramid.i18n import LocalizerRequestMixin
from pyramid.threadlocal import get_current_registry

from kotti import get_settings
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.security import get_principals
from kotti.security import SITE_ACL
from kotti.util import _
from kotti.workflow import get_workflow


def populate_users():
    """
    Create the admin user with the password from the ``kotti.secret`` option
    if there is no user with name 'admin' yet.
    """

    principals = get_principals()
    if u'admin' not in principals:
        principals[u'admin'] = {
            'name': u'admin',
            'password': get_settings()['kotti.secret'],
            'title': u"Administrator",
            'groups': [u'role:admin'],
        }


def populate():
    """
    Create the root node (:class:`~kotti.resources.Document`) and the 'about'
    subnode in the nodes tree if there are no nodes yet.
    """
    lrm = LocalizerRequestMixin()
    lrm.registry = get_current_registry()
    lrm.locale_name = get_settings()['pyramid.default_locale_name']
    localizer = lrm.localizer

    if DBSession.query(Node.id).count() == 0:
        localized_root_attrs = dict(
            [(k, localizer.translate(v)) for k, v in _ROOT_ATTRS.iteritems()])
        root = Document(**localized_root_attrs)
        root.__acl__ = SITE_ACL
        DBSession.add(root)
        localized_about_attrs = dict(
            [(k, localizer.translate(v)) for k, v in _ABOUT_ATTRS.iteritems()])
        root['about'] = Document(**localized_about_attrs)

        wf = get_workflow(root)
        if wf is not None:
            DBSession.flush()  # Initializes workflow
            wf.transition_to_state(root, None, u'public')

    populate_users()

_ROOT_ATTRS = dict(
    name=u'',  # (at the time of writing) root must have empty name!
    title=_(u'Welcome to Kotti'),
    description=_(u'Congratulations! You have successfully installed Kotti.'),
    body=_(u"""
<h2>Log in</h2>
<p>
    You can <a class="btn btn-success" href="login">log in</a> to your site
    and start changing its contents.  If you haven't chosen a password for
    your admin account yet, it'll likely be <em>qwerty</em>.
</p>
<p>
    Once you're logged in, you'll see the grey editor bar below the top
    navigation bar.  It will allow you to switch between editing and viewing the
    current page as it will appear to your visitors.
</p>
<div class="row">
    <div class="col-md-4">
        <h2>Configure</h2>
        <p>
            Find out how to configure your Kotti's title and many other
            settings using a simple text file in your file system.
        </p>
        <p>
            <a class="btn btn-info"
               href="http://kotti.readthedocs.org/en/latest/developing/basic/configuration.html">
               Configuration manual
            </a>
        </p>
    </div>
    <div class="col-md-4">
        <h2>Add-ons</h2>
        <p>
            A number of add-ons allow you to extend the functionality of your
            Kotti site.
        </p>
        <p>
            <a class="btn btn-info"
               href="http://pypi.python.org/pypi?%3Aaction=search&amp;term=kotti">
                Kotti add-ons
            </a>
        </p>
    </div>
    <div class="col-md-4">
        <h2>Documentation</h2>
        <p>
            Wonder what more you can do with Kotti?
            What license it has?
            Read the manual for more information.
        </p>
        <p>
            <a class="btn btn-info"
               href="http://kotti.readthedocs.org/en/latest/">
               Documentation
            </a>
        </p>
    </div>
</div>
"""))

_ABOUT_ATTRS = dict(
    title=_(u'About'),
    description=_(u'Our company is the leading manufacturer of foo widgets used in a wide variety of aviation and and industrial products.'),  # noqa
    body=_(u"""
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
"""))

from pkg_resources import resource_string
import os

import transaction

from kotti import get_settings
from kotti import get_version
from kotti.resources import DBSession
from kotti.resources import Node
from kotti.resources import Document
from kotti.resources import Settings
from kotti.security import get_principals
from kotti.security import SITE_ACL

def _add_document_from_file(filename, name, parent, title, package='kotti', 
                            directory='populate-content', acl=None):
    body = unicode(resource_string(package, os.path.join(directory, filename)))
    node = Document(name=name, parent=parent, title=title, body=body)
    if acl is not None:
        node.__acl__ = acl
    DBSession.add(node)
    return node

def populate_users():
    principals = get_principals()
    if u'admin' not in principals:
        principals[u'admin'] = {
            'name': u'admin',
            'password': get_settings()['kotti.secret'],
            'title': u"Administrator",
            'groups': [u'role:admin'],
            }
        DBSession.flush()
        transaction.commit()

def populate():
    nodecount = DBSession.query(Node).count()
    if nodecount == 0:
        p = _add_document_from_file(
            "home.html", u"", None, u"Welcome to Kotti!", acl=SITE_ACL)
        _add_document_from_file(
            "about.html", u"about", p, u"About")

    settingscount = DBSession.query(Settings).count()
    if settingscount == 0:
        settings = Settings(data={'kotti.db_version': get_version()})
        DBSession.add(settings)

    populate_users()
    DBSession.flush()
    transaction.commit()

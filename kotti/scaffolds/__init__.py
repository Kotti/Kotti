# -*- coding: utf-8 -*-

"""
Created on 2014-11-17
:author: Andreas Kaiser (disko)

Scaffolds for Kotti.

The methods of :class:`KottiTemplate` are marked with ``pragma: no cover``
because they are not directly touched during testsuite runs, but only within
subprocesses which seems to be not recorded by coverage.
"""

import datetime
import os

from pyramid.decorator import reify
from pyramid.scaffolds import PyramidTemplate
from textwrap import dedent
from usersettings import Settings


class KottiTemplate(PyramidTemplate):
    """ Base class for Kotti Templates """

    @reify
    def _settings(self):  # pragma: no cover
        s = Settings('org.pylonsproject.kotti.ScaffoldDefaults')
        s.add_setting("author", unicode, default='')
        s.add_setting("email", str, default='')
        s.add_setting("gh_user", str, '')
        s.load_settings()  # loads anything that might be saved

        return s

    def _get(self, key, caption):  # pragma: no cover

        env = os.environ.get(key)
        if env is not None:
            return env

        s = self._settings
        s[key] = raw_input(u'{0} [{1}]: '.format(caption, s[key])) or s[key]

        try:
            s.save_settings()
        except OSError:
            self.out("Your answers were not saved for later use.")

        return s[key]

    def pre(self, command, output_dir, vars):  # pragma: no cover
        """ Overrides :meth:`pyramid.scaffolds.PyramidTemplate.pre`, adding
        several variables to the default variables list.

        :param command: Command that invoked the template
        :type command: :class:`pyramid.scripts.pcreate.PCreateCommand`

        :param output_dir: Full filesystem path where the created package will
                           be created
        :type output_dir: str

        :param vars: Dictionary of vars passed to the templates for rendering
        :type vars: dict
        """

        vars['project_line'] = '*' * len(vars['project'])
        vars['date'] = datetime.date.today().strftime('%Y-%m-%d')

        vars['author'] = self._get('author', 'Author name')
        vars['email'] = self._get('email', 'Author email')
        vars['gh_user'] = self._get('gh_user', 'Github username')

        return PyramidTemplate.pre(self, command, output_dir, vars)

    def post(self, command, output_dir, vars):  # pragma: no cover
        """ Overrides :meth:`pyramid.scaffolds.PyramidTemplate.post`, to
        print some info after a successful scaffolding rendering."""

        separator = "=" * 79
        msg = dedent(
            u"""
            {0}
            Welcome to Kotti!

            Documentation: http://kotti.readthedocs.org/
            Development:   https://github.com/Kotti/Kotti/
            Issues:        https://github.com/Kotti/Kotti/issues?state=open
            IRC:           irc://irc.freenode.net/#kotti
            Mailing List:  https://groups.google.com/group/kotti
            {0}
        """.format(separator))

        self.out(msg)


class KottiPackageTemplate(KottiTemplate):

    _template_dir = 'package'
    summary = 'A Kotti package that can be used for a project or an add on'

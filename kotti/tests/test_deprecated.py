# -*- coding: utf-8 -*-

import warnings


def assert_deprecations(w, *msgs):

    assert len(w) == len(msgs)

    for i in range(len(w)):
        assert issubclass(w[i].category, DeprecationWarning)
        assert msgs[i] in str(w[i].message)


class TestDeprecated09:

    def test_render_tree_navigation_moved(self):
        with warnings.catch_warnings(record=True) as w:

            from kotti.views.edit.actions import render_tree_navigation
            render_tree_navigation  # pyflakes

            assert_deprecations(
                w, "has been moved to kotti.views.navigation as of Kotti 0.9")

    def test_local_navigation_moved(self):
        with warnings.catch_warnings(record=True) as w:

            from kotti.views.slots import includeme_local_navigation
            from kotti.views.slots import local_navigation
            includeme_local_navigation  # pyflakes
            local_navigation  # pyflakes

            assert_deprecations(
                w, "deprecated as of Kotti 0.9", "deprecated as of Kotti 0.9")

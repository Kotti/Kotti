# -*- coding: utf-8 -*-

import warnings


def assert_deprecations(w, *msgs):

    assert len(w) == len(msgs)

    for i in range(len(w)):
        assert issubclass(w[i].category, DeprecationWarning)
        assert msgs[i] in str(w[i].message)


class TestDeprecated10:

    def test_security_has_permission(self, allwarnings):

        with warnings.catch_warnings(record=True) as w:
            from kotti.security import has_permission
            has_permission  # pyflakes

            assert_deprecations(
                w, "deprecated as of Kotti 1.0")

from kotti.testing import UnitTestBase


class TestStatic(UnitTestBase):

    def test_NeededGroup(self):

        from kotti.static import deform_bootstrap_js
        from kotti.static import deform_js
        from kotti.static import kotti_js
        from kotti.static import NeededGroup

        def NeededGroupFactory(resources):
            return NeededGroup(resources)

        self.assertRaises(ValueError, NeededGroupFactory, "foo")
        self.assertRaises(ValueError, NeededGroupFactory, ["foo", "bar"])

        needed = NeededGroup([deform_js, kotti_js])

        assert needed.resources == [deform_js, kotti_js]

        def needed_group_adder(resource):
            needed.add(resource)

        self.assertRaises(ValueError, needed_group_adder, 42)

        needed.add(deform_bootstrap_js)

        assert needed.resources == [deform_js, kotti_js, deform_bootstrap_js]

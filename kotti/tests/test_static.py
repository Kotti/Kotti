from pytest import raises


class TestStatic:

    def test_NeededGroup(self):

        from js.deform import deform_js
        from kotti.fanstatic import contents_view_js
        from kotti.fanstatic import NeededGroup

        def NeededGroupFactory(resources):
            return NeededGroup(resources)

        with raises(ValueError):
            NeededGroupFactory("foo")
        with raises(ValueError):
            NeededGroupFactory(["foo", "bar"])

        needed = NeededGroup([deform_js, ])

        assert needed.resources == [deform_js, ]

        needed.add(contents_view_js)

        assert needed.resources == [deform_js, contents_view_js]

        def needed_group_adder(resource):
            needed.add(resource)

        with raises(ValueError):
            needed_group_adder(42)

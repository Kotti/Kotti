class TestPyramidRequestProperties:

    def test_it(self):
        from pyramid.request import Request
        from zope.interface import providedBy, implementedBy

        req = Request({})
        assert providedBy(req) == implementedBy(Request)

        req._set_properties({'b':'b'})

        assert providedBy(req) == implementedBy(Request)

    def test_subclassing(self):
        from pyramid.request import Request
        from zope.interface import providedBy, implementedBy

        class Subclass(Request):
            pass

        req = Subclass({})

        req._set_properties({'b':'b'})
        assert providedBy(req) != implementedBy(Subclass)

        #calling providedBy(req) before _set_properties makes the test pass
        req = Subclass({})
        req._set_properties({'b':'b'})
        providedBy(req)
        assert providedBy(req) == implementedBy(Subclass)


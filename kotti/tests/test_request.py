class TestExtendingRequest:

    def test_it(self):
        from kotti.request import Request
        from zope.interface import providedBy, implementedBy

        req = Request({})
        req._set_properties({'marker': 'exists'})

        assert providedBy(req) == implementedBy(Request)
        assert req.marker == 'exists'

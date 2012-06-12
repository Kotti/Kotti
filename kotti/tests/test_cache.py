import datetime

from kotti.testing import Dummy
from kotti.testing import UnitTestBase
from kotti.views.cache import set_max_age


class TestSetMaxAge(UnitTestBase):
    def test_preserve_existing_headers(self):
        response = Dummy(headers={
            "cache-control": "max-age=17,s-max-age=42,foo,bar=42"})
        delta = datetime.timedelta(days=1)
        set_max_age(response, delta)

        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == (
            "bar=42,foo,max-age=86400,s-max-age=42")

from kotti.testing import UnitTestBase


class TestImageScaleLoading(UnitTestBase):

    def test_it(self):

        from kotti.views.image import _load_image_scales, image_scales

        assert "daumennagel" not in image_scales

        _load_image_scales({"kotti.image_scales.daumennagel": "100x100"})

        self.assertEquals(image_scales["daumennagel"], [100, 100])

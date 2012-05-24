from kotti.testing import UnitTestBase


class TestImageScaleLoading(UnitTestBase):

    def test_it(self):

        from kotti.views.image import _load_image_scales, image_scales

        assert "thumb" not in image_scales

        _load_image_scales({"kotti.image_scales.thumb": "100x100"})

        self.assertEquals(image_scales["thumb"], [100, 100])

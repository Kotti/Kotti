# -*- coding: utf-8 -*-
"""
Views for image content objects.
"""
from __future__ import absolute_import, division, print_function

from zope.deprecation import deprecated

from kotti_image.views import ImageView
from kotti_image.views import _load_image_scales
from kotti_image.views import image_scales
from kotti_image.views import includeme

__ = _load_image_scales, image_scales, ImageView, includeme  # pyflakes

deprecated(('_load_image_scales', 'image_scales', 'ImageView', 'includeme'),
           'Image was outfactored to the kotti_image package.  '
           'Please import from there.')

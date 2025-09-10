from bs4 import BeautifulSoup
from plone.base.utils import safe_text
from plone.namedfile.picture import get_picture_variants
from plone.namedfile.picture import Img2PictureTag
from plone.outputfilters.interfaces import IFilter
from zope.interface import implementer

import logging


logger = logging.getLogger("plone.outputfilter.picture_variants")


@implementer(IFilter)
class PictureVariantsFilter:
    """Converts img tags with a data-picturevariant attribute into picture/source tag's with srcset definitions."""

    order = 700

    def is_enabled(self):
        return self.context is not None

    def __init__(self, context=None, request=None):
        self.current_status = None
        self.context = context
        self.request = request
        self.img2picturetag = Img2PictureTag()
        self.all_picture_variants = get_picture_variants()

    def __call__(self, data):
        soup = BeautifulSoup(safe_text(data), "html.parser")

        for elem in soup.find_all("img"):
            picture_variant_name = elem.attrs.get("data-picturevariant", "")
            if not picture_variant_name:
                continue
            picture_variants_config = self.all_picture_variants.get(
                picture_variant_name
            )
            if not picture_variants_config:
                logger.warning(
                    "Could not find the given picture_variant_name {}, leave tag untouched!".format(
                        picture_variant_name
                    )
                )
                continue
            sourceset = picture_variants_config.get("sourceset")
            if not sourceset:
                continue
            elem.replace_with(
                self.img2picturetag.create_picture_tag(sourceset, elem.attrs)
            )
        return str(soup)

import logging

from bs4 import BeautifulSoup
from plone.outputfilters.interfaces import IFilter
from Products.CMFPlone.utils import safe_nativestring
from zope.interface import implementer
from plone.namedfile.picture import Img2PictureTag, get_picture_variants

logger = logging.getLogger("plone.outputfilter.picture_variants")


@implementer(IFilter)
class PictureVariantsFilter(object):
    """Converts img tags with a data-picturevariant attribute into picture/source tag's with srcset definitions.
    """

    order = 700

    def is_enabled(self):
        if self.context is None:
            return False
        else:
            return True

    def __init__(self, context=None, request=None):
        self.current_status = None
        self.context = context
        self.request = request
        self.img2picturetag = Img2PictureTag()


    def __call__(self, data):
        soup = BeautifulSoup(safe_nativestring(data), "html.parser")

        for elem in soup.find_all("img"):
            picture_variant_name = elem.attrs.get("data-picturevariant", "")
            if not picture_variant_name:
                continue
            picture_variants_config = get_picture_variants().get(picture_variant_name)
            if not picture_variants_config:
                logger.warn(
                    "Could not find the given picture_variant_name {0}, leave tag untouched!".format(
                        picture_variant_name
                    )
                )
                continue
            sourceset = picture_variants_config.get("sourceset")
            if not sourceset:
                continue
            elem.replace_with(self.img2picturetag.create_picture_tag(sourceset, elem.attrs))
        return soup.prettify()

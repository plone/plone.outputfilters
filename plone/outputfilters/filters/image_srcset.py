import logging
import re

from bs4 import BeautifulSoup
from plone.outputfilters.interfaces import IFilter
from Products.CMFPlone.utils import safe_nativestring
from zope.interface import implementer
from plone.namedfile.picture import Img2PictureTag

logger = logging.getLogger("plone.outputfilter.image_srcset")


@implementer(IFilter)
class ImageSrcsetFilter(object):
    """Converts img tags with a data-srcset attribute into picture tag with srcset definition.
    """

    order = 700

    def _shorttag_replace(self, match):
        tag = match.group(1)
        if tag in self.singleton_tags:
            return "<" + tag + " />"
        else:
            return "<" + tag + "></" + tag + ">"

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
        data = re.sub(r"<([^<>\s]+?)\s*/>", self._shorttag_replace, data)
        soup = BeautifulSoup(safe_nativestring(data), "html.parser")

        for elem in soup.find_all("img"):
            srcset_name = elem.attrs.get("data-srcset", "")
            if not srcset_name:
                continue
            srcset_config = self.img2picturetag.image_srcsets.get(srcset_name)
            if not srcset_config:
                logger.warn(
                    "Could not find the given srcset_name {0}, leave tag untouched!".format(
                        srcset_name
                    )
                )
                continue
            sourceset = srcset_config.get("sourceset")
            if not sourceset:
                continue
            elem.replace_with(self.img2picturetag.create_picture_tag(sourceset, elem.attrs))
        return soup.prettify()

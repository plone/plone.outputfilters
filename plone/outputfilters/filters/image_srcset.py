import logging
import re

from bs4 import BeautifulSoup
from plone.base.interfaces import IImagingSchema
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.utils import safe_nativestring
from zope.component import getUtility
from zope.interface import implementer

logger = logging.getLogger("plone.outputfilter.image_srcset")


@implementer(IFilter)
class ImageSrcsetFilter(object):
    """Converts img/figure tags with a data-srcset attribute into srcset definition.
    <picture>
        <source media="(max-width:768px) and (orientation:portrait)"
                srcset="resolveuid/44d84ffd32924bb8b9dbd720f43e761c/@@images/image/teaser" />
        <source media="(max-width:768px)"
                srcset="resolveuid/44d84ffd32924bb8b9dbd720f43e761c/@@images/image/large" />
        <source media="(min-width:992px)"
                srcset="resolveuid/44d84ffd32924bb8b9dbd720f43e761c/@@images/image/larger" />
        <source media="(min-width:1200px)"
                srcset="resolveuid/44d84ffd32924bb8b9dbd720f43e761c/@@images/image/great" />
        <source media="(min-width:1400px)"
                srcset="resolveuid/44d84ffd32924bb8b9dbd720f43e761c/@@images/image/huge" />
        <img src="resolveuid/44d84ffd32924bb8b9dbd720f43e761c/@@images/image/huge" />
    </picture>
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

    @property
    def allowed_scales(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IImagingSchema, prefix="plone", check=False)
        return settings.allowed_sizes

    @property
    def image_srcsets(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IImagingSchema, prefix="plone", check=False)
        return settings.image_srcsets

    def get_scale_name(self, scale_line):
        parts = scale_line.split(" ")
        return parts and parts[0] or ""

    def get_scale_width(self, scale):
        """ get width from allowed_scales line
            large 800:65536
        """
        for s in self.allowed_scales:
            parts = s.split(" ")
            if not parts:
                continue
            if parts[0] == scale:
                dimentions = parts[1].split(":")
                if not dimentions:
                    continue
                return dimentions[0]

    def __call__(self, data):
        data = re.sub(r"<([^<>\s]+?)\s*/>", self._shorttag_replace, data)
        soup = BeautifulSoup(safe_nativestring(data), "html.parser")

        for elem in soup.find_all("img"):
            srcset_name = elem.attrs.get("data-srcset", "")
            if not srcset_name:
                continue
            elem.replace_with(self.convert_to_srcset(srcset_name, elem, soup))
        return str(soup)

    def convert_to_srcset(self, srcset_name, elem, soup):
        """Converts the element to a srcset definition"""
        srcset_config = self.image_srcsets.get(srcset_name)
        if not srcset_config:
            logger.warn(
                "Could not find the given srcset_name {0}, leave tag untouched!".format(
                    srcset_name
                )
            )
            return elem
        allowed_scales = self.allowed_scales
        sourceset = srcset_config.get("sourceset")
        if not sourceset:
            return elem
        src = elem.attrs.get("src")
        picture_tag = soup.new_tag("picture")
        css_classes = elem.attrs.get("class")
        if "captioned" in css_classes:
            picture_tag["class"] = "captioned"
        for i, source in enumerate(sourceset):
            target_scale = source["scale"]
            media = source.get("media")

            additional_scales = source.get("additionalScales", None)
            if additional_scales is None:
                additional_scales = [self.get_scale_name(s) for s in allowed_scales if s != target_scale]
            source_scales = [target_scale] + additional_scales
            source_srcset = []
            for scale in source_scales:
                scale_url = self.update_src_scale(src=src, scale=scale)
                scale_width = self.get_scale_width(scale)
                source_srcset.append("{0} {1}w".format(scale_url, scale_width))
            source_tag = soup.new_tag(
                "source", srcset=",\n".join(source_srcset)
            )
            if media:
                source_tag["media"] = media
            picture_tag.append(source_tag)
            if i == len(sourceset) - 1:
                img_tag = soup.new_tag(
                    "img", src=self.update_src_scale(src=src, scale=target_scale),
                )
                for k, attr in elem.attrs.items():
                    if k in ["src", "srcset"]:
                        continue
                    img_tag.attrs[k] = attr
                img_tag["loading"] = "lazy"
                picture_tag.append(img_tag)
        return picture_tag

    def update_src_scale(self, src, scale):
        parts = src.split("/")
        return "/".join(parts[:-1]) + "/{}".format(scale)

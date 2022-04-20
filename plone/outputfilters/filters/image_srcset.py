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
    def image_srcsets(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IImagingSchema, prefix="plone", check=False)
        return settings.image_srcsets

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
        sourceset = srcset_config.get("sourceset")
        if not sourceset:
            return elem
        src = elem.attrs.get("src")
        picture_tag = soup.new_tag("picture")
        for i, source in enumerate(sourceset):
            scale = source["scale"]
            media = source.get("media")
            sizes = source.get("sizes")
            if sizes is None:
                sizes = srcset_config.get("sizes")
            title = elem.attrs.get("title")
            alt = elem.attrs.get("alt")
            klass = elem.attrs.get("class")
            if i == len(sourceset) - 1:
                source_tag = soup.new_tag(
                    "img", src=self.update_src_scale(src=src, scale=scale)
                )
            else:
                # If sizes are defined, we add a width to the source.
                add_width = bool(sizes)
                # TODO guess type:
                source_tag = soup.new_tag(
                    "source", srcset=self.update_src_scale(src=src, scale=scale, add_width=add_width)
                )
                if sizes:
                    source_tag["sizes"] = sizes
            source_tag["loading"] = "lazy"
            if media:
                source_tag["media"] = media
            if title:
                source_tag["title"] = title
            if alt:
                source_tag["alt"] = alt
            if klass:
                source_tag["class"] = klass
            picture_tag.append(source_tag)
        return picture_tag

    def update_src_scale(self, src, scale, add_width=False):
        parts = src.split("/")
        srcset = "/".join(parts[:-1]) + "/{}".format(scale)
        if add_width:
            # add_width should only be try for source tags, not img tags.
            width = self._scale_width(scale)
            if width:
                srcset += " {}w".format(width)
        return srcset

    def _scale_width(self, scale):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IImagingSchema, prefix="plone", check=False)
        for line in settings.allowed_sizes:
            try:
                name, size = line.split()
            except (ValueError, IndexError):
                continue
            if name != scale:
                continue
            return size.split(":")[0]
        return ""

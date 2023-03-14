from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_parent
from bs4 import BeautifulSoup
from DocumentTemplate.DT_Var import newline_to_br
from DocumentTemplate.html_quote import html_quote
from plone.app.uuid.utils import uuidToObject
from plone.base.utils import safe_text
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IContentish
from urllib.parse import unquote
from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.parse import urlunsplit
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import Attribute
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces import NotFound as ztkNotFound

import re


appendix_re = re.compile("^(.*)([?#].*)$")
resolveuid_re = re.compile("^[./]*resolve[Uu]id/([^/]*)/?(.*)$")


class IImageCaptioningEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether image captioning should be performed."
    )


class IResolveUidsEnabler(Interface):
    available = Attribute("Boolean indicating whether UID links should be resolved.")


@implementer(IImageCaptioningEnabler)
class ImageCaptioningEnabler:
    @property
    def available(self):
        name = "plone.image_captioning"
        registry = getUtility(IRegistry)
        if name in registry:
            return registry[name]
        return False


@implementer(IResolveUidsEnabler)
class ResolveUidsAlwaysEnabled:
    available = True


def tag(img, **attributes):
    if hasattr(aq_base(img), "tag"):
        return img.tag(**attributes)


@implementer(IFilter)
class ResolveUIDAndCaptionFilter:
    """Parser to convert UUID links and captioned images"""

    singleton_tags = {
        "area",
        "base",
        "basefont",
        "br",
        "col",
        "command",
        "embed",
        "frame",
        "hr",
        "img",
        "input",
        "isindex",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self, context=None, request=None):
        self.current_status = None
        self.context = context
        self.request = request

    # IFilter implementation
    order = 800

    @lazy_property
    def captioned_image_template(self):
        return self.context.restrictedTraverse("plone.outputfilters_captioned_image")

    @lazy_property
    def captioned_images(self):
        for u in getAllUtilitiesRegisteredFor(IImageCaptioningEnabler):
            if u.available:
                return True
        return False

    @lazy_property
    def resolve_uids(self):
        for u in getAllUtilitiesRegisteredFor(IResolveUidsEnabler):
            if u.available:
                return True
        return False

    def is_enabled(self):
        if self.context is None:
            return False
        else:
            return True

    def _shorttag_replace(self, match):
        tag = match.group(1)
        if tag in self.singleton_tags:
            return "<" + tag + " />"
        else:
            return "<" + tag + "></" + tag + ">"

    def _render_resolveuid(self, href):
        url_parts = urlsplit(href)
        scheme = url_parts[0]
        path_parts = urlunsplit(["", ""] + list(url_parts[2:]))
        obj, subpath, appendix = self.resolve_link(path_parts)
        if obj is not None:
            href = obj.absolute_url()
            if subpath:
                href += "/" + subpath
            href += appendix
        elif (
            resolveuid_re.match(href) is None
            and not scheme
            and not href.startswith("/")
        ):
            # absolutize relative URIs; this text isn't necessarily
            # being rendered in the context where it was stored
            relative_root = self.context
            if not getattr(self.context, "isPrincipiaFolderish", False):
                relative_root = aq_parent(self.context)
            actual_url = relative_root.absolute_url()
            href = urljoin(actual_url + "/", subpath) + appendix
        return href

    def __call__(self, data):
        data = re.sub(r"<([^<>\s]+?)\s*/>", self._shorttag_replace, data)
        soup = BeautifulSoup(safe_text(data), "html.parser")
        for elem in soup.find_all(["a", "area"]):
            attributes = elem.attrs
            href = attributes.get("href")
            # an 'a' anchor element has no href
            if not href:
                continue
            if (
                not href.startswith("mailto<")
                and not href.startswith("mailto:")
                and not href.startswith("tel:")
                and not href.startswith("#")
            ):
                attributes["href"] = self._render_resolveuid(href)
        for elem in soup.find_all(["source", "img"]):
            # handles srcset attributes, not src
            # parent of SOURCE is picture here.
            # SRCSET on source/img specifies one or more images (see below).
            attributes = elem.attrs
            srcset = attributes.get("srcset")
            if not srcset:
                continue
            # https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images
            # [(src1, 480w), (src2, 360w)]
            srcs = [
                src.strip().split() for src in srcset.strip().split(",") if src.strip()
            ]
            for idx, elm in enumerate(srcs):
                image_url = elm[0]
                image, fullimage, src, description = self.resolve_image(image_url)
                srcs[idx][0] = src
            attributes["srcset"] = ",".join(" ".join(src) for src in srcs)
        for elem in soup.find_all(["source", "iframe", "audio", "video"]):
            # parent of SOURCE is video or audio here.
            # AUDIO/VIDEO can also have src attribute.
            # IFRAME is used to embed PDFs.
            attributes = elem.attrs
            src = attributes.get("src")
            if not src:
                continue
            attributes["src"] = self._render_resolveuid(src)
        for elem in soup.find_all(["img", "picture"]):
            if elem.name == "picture":
                img_elem = elem.find("img")
            else:
                img_elem = elem
            # handle src attribute
            attributes = img_elem.attrs
            src = attributes.get("src", "")
            image, fullimage, src, description = self.resolve_image(src)
            attributes["src"] = src
            if image and hasattr(image, "width"):
                if "width" not in attributes:
                    attributes["width"] = image.width
                if "height" not in attributes:
                    attributes["height"] = image.height
            if fullimage is not None:
                # Check to see if the alt / title tags need setting
                title = safe_text(aq_acquire(fullimage, "Title")())
                if not attributes.get("alt"):
                    # better an empty alt tag than none. This avoids screen readers
                    # to read the file name instead. A better fallback would be
                    # a fallback alt text coming from the img object.
                    attributes["alt"] = ""
                if "title" not in attributes:
                    attributes["title"] = title

            # handle captions
            if "captioned" in elem.attrs.get("class", []):
                caption = description
                caption_manual_override = attributes.get("data-captiontext", "")
                if caption_manual_override:
                    caption = caption_manual_override
                # Check if the image needs to be captioned
                if self.captioned_images and caption:
                    options = {}
                    options["tag"] = elem.prettify()
                    options["caption"] = newline_to_br(html_quote(caption))
                    options["class"] = " ".join(attributes["class"])
                    del attributes["class"]
                    if elem.name == "picture":
                        elem.append(img_elem)
                    captioned = BeautifulSoup(
                        self.captioned_image_template(**options), "html.parser"
                    )

                    # if we are a captioned image within a link, remove and occurrences
                    # of a tags inside caption template to preserve the outer link
                    if bool(elem.find_parent("a")) and bool(captioned.find("a")):
                        captioned.a.unwrap()
                    if elem.name == "picture":
                        del captioned.picture.img["class"]
                    else:
                        del captioned.img["class"]
                    elem.replace_with(captioned)
        return str(soup)

    def resolve_scale_data(self, url):
        """return scale url, width and height"""
        url_parts = url.split("/")
        field_name = url_parts[-2]
        scale_name = url_parts[-1]
        obj, subpath, appendix = self.resolve_link(url)
        scale_view = obj.unrestrictedTraverse("@@images", None)
        return scale_view.scale(field_name, scale_name, pre=True)

    def resolve_link(self, href):
        obj = None
        subpath = href
        appendix = ""

        # preserve querystring and/or appendix
        match = appendix_re.match(href)
        if match is not None:
            subpath, appendix = match.groups()

        if self.resolve_uids:
            match = resolveuid_re.match(subpath)
            if match is not None:
                uid, _subpath = match.groups()
                # Getting URL of an object from it's UUID needs no permission checks
                obj = uuidToObject(uid, unrestricted=True)
                if obj is not None:
                    subpath = _subpath

        return obj, subpath, appendix

    def resolve_image(self, src):
        description = ""
        if urlsplit(src)[0]:
            # We have a scheme
            return None, None, src, description
        base = self.context
        subpath = src
        appendix = ""

        def traversal_stack(base, path):
            if path.startswith("/"):
                base = getSite()
                path = path[1:]
            obj = base
            stack = [obj]
            components = path.split("/")
            # print("components: {}".format(components))
            while components:
                child_id = unquote(components.pop(0))
                try:
                    if hasattr(aq_base(obj), "scale"):
                        if components:
                            child = obj.scale(child_id, components.pop(), pre=True)
                        else:
                            child = obj.scale(child_id, pre=True)
                    else:
                        # Do not use restrictedTraverse here; the path to the
                        # image may lead over containers that lack the View
                        # permission for the current user!
                        # Also, if the image itself is not viewable, we rather
                        # show a broken image than hide it or raise
                        # unauthorized here (for the referring document).
                        child = obj.unrestrictedTraverse(str(child_id))
                except ConflictError:
                    raise
                except (AttributeError, KeyError, NotFound, ztkNotFound):
                    return
                obj = child
                stack.append(obj)
            # print(f"traversal_stack: {stack}")
            return stack

        def traverse_path(base, path):
            stack = traversal_stack(base, path)
            if stack is None:
                return
            return stack[-1]

        obj, subpath, appendix = self.resolve_link(src)
        if obj is not None:
            # resolved uid
            fullimage = obj
            image = None
            if not subpath:
                image = traverse_path(fullimage, "@@images/image")
            if image is None:
                image = traverse_path(fullimage, subpath)
        elif "/@@" in subpath:
            # split on view
            pos = subpath.find("/@@")
            fullimage = traverse_path(base, subpath[:pos])
            if fullimage is None:
                return None, None, src, description
            image = traverse_path(fullimage, subpath[pos + 1 :])
        else:
            stack = traversal_stack(base, subpath)
            if stack is None:
                return None, None, src, description
            image = stack.pop()
            # if it's a scale, find the full image by traversing one less
            fullimage = image
            if not IContentish.providedBy(fullimage):
                stack.reverse()
                for parent in stack:
                    if hasattr(aq_base(parent), "tag"):
                        fullimage = parent
                        break
            if not hasattr(image, "width"):
                image_scale = traverse_path(image, "@@images/image")
                if image_scale:
                    image = image_scale

        if image is None:
            return None, None, src, description
        try:
            url = image.absolute_url()
        except AttributeError:
            return None, None, src, description
        src = url + appendix
        description = safe_text(aq_acquire(fullimage, "Description")())
        return image, fullimage, src, description

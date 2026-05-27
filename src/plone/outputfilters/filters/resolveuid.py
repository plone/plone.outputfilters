from Acquisition import aq_base
from Acquisition import aq_parent
from bs4 import BeautifulSoup
from plone.base.utils import safe_text
from plone.outputfilters.interfaces import IFilter
from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.parse import urlunsplit
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getAllUtilitiesRegisteredFor
from zope.interface import Attribute
from zope.interface import implementer
from zope.interface import Interface

import re

appendix_re = re.compile("^(.*)([?#].*)$")
resolveuid_re = re.compile("^[./]*resolve[Uu]id/([^/]*)/?(.*)$")


class IResolveUidsEnabler(Interface):
    available = Attribute("Boolean indicating whether UID links should be resolved.")


@implementer(IResolveUidsEnabler)
class ResolveUidsAlwaysEnabled:
    available = True


def tag(img, **attributes):
    if hasattr(aq_base(img), "tag"):
        return img.tag(**attributes)


@implementer(IFilter)
class ResolveUIDFilter:
    """Parser to convert UUID links"""

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
        for elem in soup.find_all(["source", "iframe", "audio", "video"]):
            # parent of SOURCE is video or audio here.
            # AUDIO/VIDEO can also have src attribute.
            # IFRAME is used to embed PDFs.
            attributes = elem.attrs
            src = attributes.get("src")
            if not src:
                continue
            attributes["src"] = self._render_resolveuid(src)
        return str(soup)

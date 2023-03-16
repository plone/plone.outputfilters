from Acquisition import aq_base
from plone.app.uuid.utils import uuidToObject as new_uuidToObject
from Products.CMFCore.utils import getToolByName
from zExceptions import NotFound
from zope.deprecation import deprecate
from zope.interface import implementer
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces import IPublishTraverse


try:
    from zope.component.hooks import getSite
except ImportError:
    from zope.app.component.hooks import getSite


@deprecate(
    "Please use plone.app.uuid.utils.uuidToURL instead. Will be removed in Plone 7"
)
def uuidToURL(uuid):
    """Resolves a UUID to a URL via the UID index of portal_catalog."""
    catalog = getToolByName(getSite(), "portal_catalog")
    res = catalog.unrestrictedSearchResults(UID=uuid)
    if res:
        return res[0].getURL()


@deprecate("Import from plone.app.uuid.utils instead. Will be removed in Plone 7")
def uuidToObject(uuid):
    """Resolves a UUID to an object via the Physical Path"""
    return new_uuidToObject(uuid, unrestricted=True)


try:
    from plone.uuid.interfaces import IUUID
except ImportError:

    def uuidFor(obj):
        return obj.UID()

else:

    def uuidFor(obj):
        uuid = IUUID(obj, None)
        if uuid is None and hasattr(aq_base(obj), "UID"):
            uuid = obj.UID()
        return uuid


@implementer(IPublishTraverse)
class ResolveUIDView(BrowserView):
    """Resolve a URL like /resolveuid/<uuid> to a normalized URL."""

    subpath = None

    def publishTraverse(self, request, name):
        self.uuid = name
        traverse_subpath = self.request["TraversalRequestNameStack"]
        if traverse_subpath:
            traverse_subpath = list(traverse_subpath)
            traverse_subpath.reverse()
            self.subpath = traverse_subpath
            self.request["TraversalRequestNameStack"] = []
        return self

    def __call__(self):
        url = uuidToURL(self.uuid)

        if not url:
            raise NotFound("The link you followed is broken")

        if self.subpath:
            url = "/".join([url] + self.subpath)

        if self.request.QUERY_STRING:
            url += "?" + self.request.QUERY_STRING

        self.request.response.redirect(url, status=301)

        return ""

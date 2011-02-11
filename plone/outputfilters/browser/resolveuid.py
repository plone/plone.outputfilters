from zExceptions import NotFound
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.browser import BrowserView
from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName

# Here is a bunch of BBB stuff so that we can continue to work with
# Plone 3 without requiring plone.app.uuid.  If Plone 3 support is
# dropped in the editors that depend on plone.outputfilters, then
# code can be updated to simply use the functions from plone.app.uuid


def BBB_uuidToURL(uuid):
    """Resolves a UUID to a URL via the UID catalog index.

    Provided for compatibility when plone.app.uuid is not present.
    """
    catalog = getToolByName(getSite(), 'portal_catalog')
    res = catalog(UID=uuid)
    if res:
        return res[0].getURL()


def BBB_uuidToObject(uuid):
    """Resolves a UUID to an object via the UID catalog index.

    Provided for compatibility when plone.app.uuid is not present.
    """
    catalog = getToolByName(getSite(), 'portal_catalog')
    res = catalog(UID=uuid)
    if res:
        return res[0].getObject()

try:
    from plone.app.uuid.utils import uuidToURL
    from plone.app.uuid.utils import uuidToObject
except ImportError:
    uuidToURL = BBB_uuidToURL
    uuidToObject = BBB_uuidToObject
    def uuidFor(obj):
        return obj.UID()
else:
    from plone.uuid.interfaces import IUUID
    def uuidFor(obj):
        return IUUID(obj, None)


class ResolveUIDView(BrowserView):
    """Resolve a URL like /resolveuid/<uuid> to a normalized URL.
    """
    implements(IPublishTraverse)

    subpath = None

    def publishTraverse(self, request, name):
        self.uuid = name
        traverse_subpath = self.request['TraversalRequestNameStack']
        if traverse_subpath:
            traverse_subpath = list(traverse_subpath)
            traverse_subpath.reverse()
            self.subpath = traverse_subpath
            self.request['TraversalRequestNameStack'] = []
        return self

    def __call__(self):
        url = uuidToURL(self.uuid)

        if not url:
            # BBB for kupu
            hook = getattr(self.context, 'kupu_resolveuid_hook', None)
            if hook:
                obj = hook(uuid)
                if not obj:
                    raise NotFound("The link you followed is broken")
                url = obj.absolute_url()

        if not url:
            raise NotFound("The link you followed is broken")

        if self.subpath:
            url = '/'.join([url] + self.subpath)

        if self.request.QUERY_STRING:
            url += '?' + self.request.QUERY_STRING

        self.request.response.redirect(url, status=301)

        return ''

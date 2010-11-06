from zExceptions import NotFound
from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.browser import BrowserView
from zope.app.component.hooks import getSite
from Products.CMFCore.utils import getToolByName


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


class ResolveUIDView(BrowserView):
    """Resolve a URL like /resolveuid/<uuid> to a normalized URL.
    """
    implements(IPublishTraverse)
    
    def publishTraverse(self, request, name):
        uuid = name
        url = uuidToURL(uuid)
        
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

        traverse_subpath = self.request['TraversalRequestNameStack']
        if traverse_subpath:
            url = '/'.join([url] + traverse_subpath)
            self.request['TraversalRequestNameStack'] = []

        if self.request.QUERY_STRING:
            url += '?' + self.request.QUERY_STRING

        self.request.response.redirect(url, status=301)
        return self

    def __call__(self):
        return ''

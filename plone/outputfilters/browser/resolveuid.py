# -*- coding: utf-8 -*-
from Acquisition import aq_base
from plone.app.uuid.utils import uuidToURL
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from zExceptions import NotFound
from zope.component.hooks import getSite
from zope.deprecation import deprecate
from zope.interface import implementer
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces import IPublishTraverse

import zope.deferredimport


zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from plone.app.uuid.utils instead",
    uuidToObject='plone.app.uuid:utils.uuidToObject',
    # This does not seem to work, since we need it ourselves in this file:
    # uuidToURL='plone.app.uuid:utils.uuidToURL',
)


@deprecate('uuidFor is no longer used and supported, will be removed in Plone 7.')
def uuidFor(obj):
    uuid = IUUID(obj, None)
    if uuid is None and hasattr(aq_base(obj), 'UID'):
        uuid = obj.UID()
    return uuid


@implementer(IPublishTraverse)
class ResolveUIDView(BrowserView):
    """Resolve a URL like /resolveuid/<uuid> to a normalized URL.
    """

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
            raise NotFound("The link you followed is broken")

        if self.subpath:
            url = '/'.join([url] + self.subpath)

        if self.request.QUERY_STRING:
            url += '?' + self.request.QUERY_STRING

        self.request.response.redirect(url, status=301)

        return ''

# -*- coding: utf-8 -*-
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_parent
from bs4 import BeautifulSoup
from DocumentTemplate.DT_Util import html_quote
from DocumentTemplate.DT_Var import newline_to_br
from plone.outputfilters.browser.resolveuid import uuidToObject
from plone.outputfilters.interfaces import IFilter
from Products.CMFCore.interfaces import IContentish
from Products.CMFPlone.utils import safe_unicode
from six.moves.urllib.parse import unquote
from six.moves.urllib.parse import urljoin
from six.moves.urllib.parse import urlsplit
from six.moves.urllib.parse import urlunsplit
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getAllUtilitiesRegisteredFor
from zope.component.hooks import getSite
from zope.interface import Attribute
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces import NotFound as ztkNotFound

import re
import six


HAS_LINGUAPLONE = True
try:
    from Products.LinguaPlone.utils import translated_references
except ImportError:
    HAS_LINGUAPLONE = False


appendix_re = re.compile('^(.*)([?#].*)$')
resolveuid_re = re.compile('^[./]*resolve[Uu]id/([^/]*)/?(.*)$')


class IImageCaptioningEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether image captioning should be performed.")


class IResolveUidsEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether UID links should be resolved.")


@implementer(IResolveUidsEnabler)
class ResolveUidsAlwaysEnabled(object):

    available = True


def tag(img, **attributes):
    if hasattr(aq_base(img), 'tag'):
        return img.tag(**attributes)


@implementer(IFilter)
class ResolveUIDAndCaptionFilter(object):
    """ Parser to convert UUID links and captioned images """

    singleton_tags = set([
        'area', 'base', 'basefont', 'br', 'col', 'command', 'embed', 'frame',
        'hr', 'img', 'input', 'isindex', 'keygen', 'link', 'meta', 'param',
        'source', 'track', 'wbr'])

    def __init__(self, context=None, request=None):
        self.current_status = None
        self.context = context
        self.request = request

    # IFilter implementation
    order = 800

    @lazy_property
    def captioned_image_template(self):
        return self.context.restrictedTraverse(
            'plone.outputfilters_captioned_image')

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
            return '<' + tag + ' />'
        else:
            return '<' + tag + '></' + tag + '>'

    def __call__(self, data):
        data = re.sub(r'<([^<>\s]+?)\s*/>', self._shorttag_replace, data)
        soup = BeautifulSoup(safe_unicode(data), 'html.parser')

        for elem in soup.find_all(['a', 'area']):
            attributes = elem.attrs
            href = attributes.get('href')
            # an 'a' anchor element has no href
            if not href:
                continue
            url_parts = urlsplit(href)
            scheme = url_parts[0]
            # we are only interested in path and beyond /foo/bar?x=2#abc
            path_parts = urlunsplit(['', ''] + list(url_parts[2:]))
            if not href.startswith('mailto<') \
                    and not href.startswith('mailto:') \
                    and not href.startswith('tel:') \
                    and not href.startswith('#'):
                obj, subpath, appendix = self.resolve_link(path_parts)
                if obj is not None:
                    href = obj.absolute_url()
                    if subpath:
                        href += '/' + subpath
                    href += appendix
                elif resolveuid_re.match(href) is None \
                        and not scheme \
                        and not href.startswith('/'):
                    # absolutize relative URIs; this text isn't necessarily
                    # being rendered in the context where it was stored
                    relative_root = self.context
                    if not getattr(
                            self.context, 'isPrincipiaFolderish', False):
                        relative_root = aq_parent(self.context)
                    actual_url = relative_root.absolute_url()
                    href = urljoin(actual_url + '/', subpath) + appendix
                attributes['href'] = href
        for elem in soup.find_all('img'):
            attributes = elem.attrs
            src = attributes.get('src', '')
            image, fullimage, src, description = self.resolve_image(src)
            attributes["src"] = src

            if fullimage is not None:
                # Check to see if the alt / title tags need setting
                title = safe_unicode(aq_acquire(fullimage, 'Title')())
                if not attributes.get('alt'):
                    # XXX alt attribute contains *alternate* text
                    attributes['alt'] = description or title
                if 'title' not in attributes:
                    attributes['title'] = title

            caption = description
            # Check if the image needs to be captioned
            if (
                self.captioned_images and
                image is not None and
                caption and
                'captioned' in attributes.get('class', [])
            ):
                self.handle_captioned_image(
                    attributes, image, fullimage, elem, caption)
        return six.text_type(soup)

    def lookup_uid(self, uid):
        context = self.context
        if HAS_LINGUAPLONE:
            # If we have LinguaPlone installed, add support for language-aware
            # references
            uids = translated_references(context, context.Language(), uid)
            if len(uids) > 0:
                uid = uids[0]
        return uuidToObject(uid)

    def resolve_link(self, href):
        obj = None
        subpath = href
        appendix = ''

        # preserve querystring and/or appendix
        match = appendix_re.match(href)
        if match is not None:
            subpath, appendix = match.groups()

        if self.resolve_uids:
            match = resolveuid_re.match(subpath)
            if match is not None:
                uid, _subpath = match.groups()
                obj = self.lookup_uid(uid)
                if obj is not None:
                    subpath = _subpath

        return obj, subpath, appendix

    def resolve_image(self, src):
        description = ''
        if urlsplit(src)[0]:
            # We have a scheme
            return None, None, src, description

        base = self.context
        subpath = src
        appendix = ''

        def traversal_stack(base, path):
            if path.startswith('/'):
                base = getSite()
                path = path[1:]
            obj = base
            stack = [obj]
            components = path.split('/')
            while components:
                child_id = unquote(components.pop(0))
                try:
                    if hasattr(aq_base(obj), 'scale'):
                        if components:
                            child = obj.scale(child_id, components.pop())
                        else:
                            child = obj.scale(child_id)
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
            image = traverse_path(fullimage, subpath)
        elif '/@@' in subpath:
            # split on view
            pos = subpath.find('/@@')
            fullimage = traverse_path(base, subpath[:pos])
            if fullimage is None:
                return None, None, src, description
            image = traverse_path(fullimage, subpath[pos + 1:])
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
                    if hasattr(aq_base(parent), 'tag'):
                        fullimage = parent
                        break

        if image is None:
            return None, None, src, description

        try:
            url = image.absolute_url()
        except AttributeError:
            return None, None, src, description
        src = url + appendix
        description = safe_unicode(aq_acquire(fullimage, 'Description')())
        return image, fullimage, src, description

    def handle_captioned_image(self, attributes, image, fullimage,
                               elem, caption):
        """Handle captioned image.

        The img element is replaced by a definition list
        as created by the template ../browser/captioned_image.pt
        """
        klass = ' '.join(attributes['class'])
        del attributes['class']
        del attributes['src']
        if 'width' in attributes:
            attributes['width'] = int(attributes['width'])
        if 'height' in attributes:
            attributes['height'] = int(attributes['height'])
        view = fullimage.unrestrictedTraverse('@@images', None)
        if view is not None:
            original_width, original_height = view.getImageSize()
        else:
            original_width, original_height = fullimage.width, fullimage.height
        if image is not fullimage:
            # image is a scale object
            tag = image.tag
            width = image.width
        else:
            if hasattr(aq_base(image), 'tag'):
                tag = image.tag
            else:
                tag = view.scale().tag
            width = original_width
        options = {
            'class': klass,
            'originalwidth': attributes.get('width', None),
            'originalalt': attributes.get('alt', None),
            'url_path': fullimage.absolute_url_path(),
            'caption': newline_to_br(html_quote(caption)),
            'image': image,
            'fullimage': fullimage,
            'tag': tag(**attributes),
            'isfullsize': image is fullimage or (
                image.width == original_width and
                image.height == original_height),
            'width': attributes.get('width', width),
        }

        captioned = BeautifulSoup(
            self.captioned_image_template(**options), 'html.parser')

        # if we are a captioned image within a link, remove and occurrences
        # of a tags inside caption template to preserve the outer link
        if bool(elem.find_parent('a')):
            captioned.a.unwrap()

        elem.replace_with(captioned)

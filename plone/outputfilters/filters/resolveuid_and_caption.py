# -*- coding: utf-8 -*-
from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_parent
from cgi import escape
from DocumentTemplate.DT_Util import html_quote
from DocumentTemplate.DT_Var import newline_to_br
from plone.outputfilters.browser.resolveuid import uuidToObject
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IContentish
from sgmllib import SGMLParseError
from sgmllib import SGMLParser
from six.moves.urllib.parse import unquote
from six.moves.urllib.parse import urljoin
from six.moves.urllib.parse import urlsplit
from six.moves.urllib.parse import urlunsplit
from unidecode import unidecode
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
import six


HAS_LINGUAPLONE = True
try:
    from Products.LinguaPlone.utils import translated_references
except ImportError:
    HAS_LINGUAPLONE = False


appendix_re = re.compile('^(.*)([\?#].*)$')
resolveuid_re = re.compile('^[./]*resolve[Uu]id/([^/]*)/?(.*)$')


class IImageCaptioningEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether image captioning should be performed.")


class IResolveUidsEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether UID links should be resolved.")


@implementer(IImageCaptioningEnabler)
class ImageCaptioningEnabler(object):

    @property
    def available(self):
        name = 'plone.image_captioning'
        registry = getUtility(IRegistry)
        if name in registry:
            return registry[name]
        return False


@implementer(IResolveUidsEnabler)
class ResolveUidsAlwaysEnabled(object):

    available = True


def tag(img, **attributes):
    if hasattr(aq_base(img), 'tag'):
        return img.tag(**attributes)


@implementer(IFilter)
class ResolveUIDAndCaptionFilter(SGMLParser):
    """ Parser to convert UUID links and captioned images """

    singleton_tags = set([
        'area', 'base', 'basefont', 'br', 'col', 'command', 'embed', 'frame',
        'hr', 'img', 'input', 'isindex', 'keygen', 'link', 'meta', 'param',
        'source', 'track', 'wbr'])

    def __init__(self, context=None, request=None):
        SGMLParser.__init__(self)
        self.current_status = None
        self.context = context
        self.request = request
        self.pieces = []
        self.in_link = False
        self.in_script = False

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
        self.feed(data)
        self.close()
        return self.getResult()

    # SGMLParser implementation

    def append_data(self, data, add_eol=0):
        """Append data unmodified to self.data, add_eol adds a newline
        character"""
        if add_eol:
            data += '\n'
        self.pieces.append(data)

    def handle_charref(self, ref):
        """ Handle characters, just add them again """
        self.append_data("&#%s;" % ref)

    def handle_entityref(self, ref):
        """ Handle html entities, put them back as we get them """
        self.append_data("&%s;" % ref)

    def handle_data(self, text):
        """ Add data unmodified """
        self.append_data(text)

    def handle_comment(self, text):
        """ Handle comments unmodified """
        self.append_data("<!--%s-->" % text)

    def handle_pi(self, text):
        """ Handle processing instructions unmodified"""
        self.append_data("<?%s>" % text)

    def handle_decl(self, text):
        """Handle declarations unmodified """
        self.append_data("<!%s>" % text)

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
        if isinstance(url, six.text_type):
            url = url.encode('utf8')
        src = url + appendix
        description = aq_acquire(fullimage, 'Description')()
        return image, fullimage, src, description

    def handle_captioned_image(self, attributes, image, fullimage, caption):
        """Handle captioned image.
        """
        klass = attributes['class']
        del attributes['class']
        del attributes['src']
        if 'width' in attributes and attributes['width']:
            attributes['width'] = int(attributes['width'])
        if 'height' in attributes and attributes['height']:
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
        if self.in_link:
            # Must preserve original link, don't overwrite
            # with a link to the image
            options['isfullsize'] = True

        captioned_html = self.captioned_image_template(**options)
        if isinstance(captioned_html, six.text_type):
            captioned_html = captioned_html.encode('utf8')
        self.append_data(captioned_html)

    def unknown_starttag(self, tag, attrs):
        """Here we've got the actual conversion of links and images.

        Convert UUID's to absolute URLs, and process captioned images to HTML.
        """
        if tag == 'script':
            self.in_script = True
        if tag in ['a', 'img', 'area'] and not self.in_script:
            # Only do something if tag is a link, image, or image map area.

            attributes = dict(attrs)
            if tag == 'a':
                self.in_link = True
            if (tag == 'a' or tag == 'area') and 'href' in attributes:
                href = attributes['href']
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
                    attrs = six.iteritems(attributes)
            elif tag == 'img':
                src = attributes.get('src', '')
                image, fullimage, src, description = self.resolve_image(src)
                attributes["src"] = src
                caption = description
                # Check if the image needs to be captioned
                if (
                    self.captioned_images and
                    image is not None and
                    caption and
                    'captioned' in attributes.get('class', '').split(' ')
                ):
                    self.handle_captioned_image(attributes, image, fullimage,
                                                caption)
                    return True
                if fullimage is not None:
                    # Check to see if the alt / title tags need setting
                    title = aq_acquire(fullimage, 'Title')()
                    if not attributes.get('alt'):
                        attributes['alt'] = description or title
                    if 'title' not in attributes:
                        attributes['title'] = title
                    attrs = six.iteritems(attributes)

        # Add the tag to the result
        strattrs = ""
        for key, value in attrs:
            try:
                strattrs += ' %s="%s"' % (key, escape(value, quote=True))
            except UnicodeDecodeError:
                strattrs += ' %s="%s"' % (unidecode(key),
                                          escape(unidecode(value), quote=True))

        if tag in self.singleton_tags:
            self.append_data("<%s%s />" % (tag, strattrs))
        else:
            self.append_data("<%s%s>" % (tag, strattrs))

    def unknown_endtag(self, tag):
        """Add the endtag unmodified"""
        if tag == 'a':
            self.in_link = False
        if tag == 'script':
            self.in_script = False
        self.append_data("</%s>" % tag)

    def parse_declaration(self, i):
        """Fix handling of CDATA sections. Code borrowed from BeautifulSoup.
        """
        j = None
        if self.rawdata[i:i + 9] == '<![CDATA[':
            k = self.rawdata.find(']]>', i)
            if k == -1:
                k = len(self.rawdata)
            data = self.rawdata[i + 9:k]
            j = k + 3
            self.append_data("<![CDATA[%s]]>" % data)
        else:
            try:
                j = SGMLParser.parse_declaration(self, i)
            except SGMLParseError:
                toHandle = self.rawdata[i:]
                self.handle_data(toHandle)
                j = i + len(toHandle)
        return j

    def getResult(self):
        """Return the parsed result and flush it"""
        result = "".join(self.pieces)
        self.pieces = None
        return result

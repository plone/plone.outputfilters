from Acquisition import aq_base
from DocumentTemplate.DT_Util import html_quote
from DocumentTemplate.DT_Var import newline_to_br
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import getAllUtilitiesRegisteredFor
from zope.interface import implements, Interface, Attribute
from plone.outputfilters.browser.resolveuid import uuidToObject

from urlparse import urljoin
from sgmllib import SGMLParser, SGMLParseError

HAS_LINGUAPLONE = True
try:
    from Products.LinguaPlone.utils import translated_references
except ImportError:
    HAS_LINGUAPLONE = False

from plone.outputfilters.interfaces import IFilter


class IImageCaptioningEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether image captioning should be performed.")


class IResolveUidsEnabler(Interface):
    available = Attribute(
        "Boolean indicating whether UID links should be resolved.")

singleton_tags = ["img", "area", "br", "hr", "input", "meta", "param", "col"]


class ResolveUIDAndCaptionFilter(SGMLParser):
    """ Parser to convert UUID links and captioned images """
    implements(IFilter)

    def __init__(self, context=None, request=None):
        SGMLParser.__init__(self)
        self.current_status = None
        self.context = context
        self.request = request
        self.pieces = []
        self.captioned_image_template = context.restrictedTraverse(
            'plone.outputfilters_captioned_image')
        self.in_link = False

    # IFilter implementation
    order = 800

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
        return self.captioned_images or self.resolve_uids

    def __call__(self, data):
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
        subpath = ''
        appendix = ''

        # preserve querystring and/or appendix
        for char in ('#', '?'):
            parts = href.split(char)
            href = parts[0]
            if len(parts) > 1:
                appendix += char + char.join(parts[1:])

        if 'resolveuid' in href:
            # get the UUID
            parts = href.split('/')
            uid = parts[1]
            if len(parts) > 2:
                subpath = '/'.join(parts[2:])

            obj = self.lookup_uid(uid)

        return obj, subpath, appendix

    def resolve_image(self, src):
        image = fullimage = None
        description = ''
        base = self.context
        subpath = src
        appendix = ''

        if 'resolveuid' in src:
            base, subpath, appendix = self.resolve_link(src)

        # let's see if we can traverse to the image
        try:
            image = base.restrictedTraverse(subpath)
        except:
            return None, None, src, ''

        fullimage = image
        src = image.absolute_url() + appendix
        if image and hasattr(aq_base(image), 'Description'):
            description = image.Description()
        elif image and subpath:
            # maybe it's an image scale; try traversing one less
            parent_path = '/'.join(subpath.split('/')[:-1])
            try:
                fullimage = base.restrictedTraverse(parent_path)
            except:
                pass
            if fullimage and hasattr(aq_base(fullimage), 'Description'):
                description = fullimage.Description()

        return image, fullimage, src, description

    def handle_captioned_image(self, attributes, image, fullimage, caption):
        """Handle captioned image.
        """
        klass = attributes['class']
        del attributes['class']
        del attributes['src']
        options = {
            'class': klass,
            'originalwidth': attributes.get('width', None),
            'originalalt': attributes.get('alt', None),
            'url_path': fullimage.absolute_url_path(),
            'caption': newline_to_br(html_quote(caption)),
            'image': image,
            'fullimage': fullimage,
            'tag': image.tag(**attributes),
            'isfullsize': (image.width == fullimage.width and
                           image.height == fullimage.height),
            'width': attributes.get('width', image.width),
            }
        if self.in_link:
            # Must preserve original link, don't overwrite
            # with a link to the image
            options['isfullsize'] = True

        captioned_html = self.captioned_image_template(**options)
        if isinstance(captioned_html, unicode):
            captioned_html = captioned_html.encode('utf8')
        self.append_data(captioned_html)

    def unknown_starttag(self, tag, attrs):
        """Here we've got the actual conversion of links and images.

        Convert UUID's to absolute URLs, and process captioned images to HTML.
        """
        if tag in ['a', 'img', 'area']:
            # Only do something if tag is a link, image, or image map area.

            attributes = {}
            for (key, value) in attrs:
                attributes[key] = value

            if tag == 'a':
                self.in_link = True
            if (tag == 'a' or tag == 'area') and 'href' in attributes:
                href = attributes['href']
                if self.resolve_uids and 'resolveuid' in href:
                    obj, subpath, appendix = self.resolve_link(href)
                    if obj:
                        href = obj.absolute_url()
                        if subpath:
                            href += '/' + subpath
                        href += appendix
                elif not href.startswith('http') and not href.startswith('/'):
                    # absolutize relative URIs; this text isn't necessarily
                    # being rendered in the context where it was stored
                    obj, subpath, appendix = self.resolve_link(href)
                    href = urljoin(self.context.absolute_url() + '/',
                                   href) + appendix
                attributes['href'] = href
                attrs = attributes.iteritems()
            elif tag == 'img':
                src = attributes.get('src', '')
                image, fullimage, src, description = self.resolve_image(src)
                attributes["src"] = src
                caption = description

                # Check if the image needs to be captioned
                if (self.captioned_images and image and caption
                    and 'captioned' in attributes.get('class', '').split(' ')):
                    self.handle_captioned_image(attributes, image, fullimage,
                                                caption)
                    return True
                else:
                    # Nothing happens with the image, so add it normally
                    attrs = attributes.iteritems()

        # Add the tag to the result
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])
        if tag in singleton_tags:
            self.append_data("<%s%s />" % (tag, strattrs))
        else:
            self.append_data("<%s%s>" % (tag, strattrs))

    def unknown_endtag(self, tag):
        """Add the endtag unmodified"""
        if tag == 'a':
            self.in_link = False
        self.append_data("</%s>" % tag)

    def parse_declaration(self, i):
        """Fix handling of CDATA sections. Code borrowed from BeautifulSoup.
        """
        j = None
        if self.rawdata[i:i+9] == '<![CDATA[':
            k = self.rawdata.find(']]>', i)
            if k == -1:
                k = len(self.rawdata)
            data = self.rawdata[i+9:k]
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

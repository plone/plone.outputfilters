from doctest import _ellipsis_match
from doctest import OutputChecker
from doctest import REPORT_NDIFF
from os.path import abspath
from os.path import dirname
from os.path import join
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing.bbb import PloneTestCase
from plone.outputfilters.filters.resolveuid_and_caption import ResolveUIDAndCaptionFilter  # noqa
from plone.outputfilters.testing import PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING
from Products.PortalTransforms.tests.utils import normalize_html

import pkg_resources


# plone.namedfile is not part of coredev (yet) as such
# it is not hard dependency
try:
    pkg_resources.get_distribution('plone.namedfile')
except pkg_resources.DistributionNotFound:
    HAS_NAMEDFILE = False
else:
    from plone.namedfile.file import NamedImage
    from plone.namedfile.tests.test_scaling import DummyContent as NFDummyContent  # noqa
    HAS_NAMEDFILE = True


PREFIX = abspath(dirname(__file__))


def dummy_image():
    from plone.namedfile.file import NamedBlobImage
    filename = join(PREFIX, u'image.jpg')
    data = open(filename, 'rb').read()
    return NamedBlobImage(data=data, filename=filename)


class ResolveUIDAndCaptionFilterIntegrationTestCase(PloneTestCase):

    layer = PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING

    image_id = 'image.jpg'

    def _makeParser(self, **kw):
        parser = ResolveUIDAndCaptionFilter(context=self.portal)
        for k, v in kw.items():
            setattr(parser, k, v)
        return parser

    def _makeDummyContent(self):
        from OFS.SimpleItem import SimpleItem

        class DummyContent(SimpleItem):

            def __init__(self, id):
                self.id = id

            def UID(self):
                return 'foo'

            allowedRolesAndUsers = ('Anonymous',)

        if HAS_NAMEDFILE:
            class DummyContent2(NFDummyContent):
                id = __name__ = title = 'foo2'

                def UID(self):
                    return 'foo2'

        dummy = DummyContent('foo')
        self.portal._setObject('foo', dummy)
        self.portal.portal_catalog.catalog_object(self.portal.foo)

        if HAS_NAMEDFILE:
            dummy2 = DummyContent2('foo2')
            data = open(join(PREFIX, self.image_id), 'rb').read()
            dummy2.image = NamedImage(data, 'image/jpeg', u'image.jpeg')
            self.portal._setObject('foo2', dummy2)
            self.portal.portal_catalog.catalog_object(self.portal.foo2)

    def _assertTransformsTo(self, input, expected):
        # compare two chunks of HTML ignoring whitespace differences,
        # and with a useful diff on failure
        out = self.parser(input)
        normalized_out = normalize_html(out)
        normalized_expected = normalize_html(expected)
        try:
            self.assertTrue(_ellipsis_match(normalized_expected,
                                            normalized_out))
        except AssertionError:
            class wrapper(object):
                want = expected
            raise AssertionError(self.outputchecker.output_difference(
                wrapper, out, REPORT_NDIFF))

    def afterSetUp(self):
        # create an image and record its UID
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        if self.image_id not in self.portal:
            self.portal.invokeFactory(
                'Image', id=self.image_id, title='Image')
        image = self.portal[self.image_id]
        image.setDescription('My caption')
        image.image = dummy_image()
        image.reindexObject()
        self.UID = image.UID()
        self.parser = self._makeParser(captioned_images=True,
                                       resolve_uids=True)
        assert self.parser.is_enabled()

        self.outputchecker = OutputChecker()

    def beforeTearDown(self):
        self.login()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        del self.portal[self.image_id]

    def test_parsing_minimal(self):
        text = '<div>Some simple text.</div>'
        res = self.parser(text)
        self.assertEqual(text, str(res))

    def test_parsing_preserves_newlines(self):
        # Test if it preserves newlines which should not be filtered out
        text = """<pre>This is line 1
This is line 2</pre>"""
        res = self.parser(text)
        self.assertEqual(text, str(res))

    def test_parsing_preserves_CDATA(self):
        # Test if it preserves CDATA sections, such as those TinyMCE puts into
        # script tags. The standard SGMLParser has a bug that will remove
        # these.
        text = """<p>hello</p>
<script type="text/javsacript">// <![CDATA[
alert(1);
// ]]></script>
<p>world</p>"""
        res = self.parser(text)
        self.assertEqual(text, str(res))

    def test_resolve_uids_in_links(self):
        text = """<html>
  <head></head>
  <body>
    <a class="internal-link" href="resolveuid/%s">Some link</a>
    <a class="internal-link" href="resolveuid/%s#named-anchor">Some anchored link</a>
  </body>
</html>""" % (self.UID, self.UID)
        res = self.parser(text)
        self.assertTrue('href="http://nohost/plone/image.jpg"' in str(res))
        self.assertTrue('href="http://nohost/plone/image.jpg#named-anchor"'
                        in str(res))

    def test_resolve_uids_relative_link(self):
        text_in = """<a href="../resolveuid/%s">foo</a>""" % self.UID
        text_out = """<a href="http://nohost/plone/image.jpg">foo</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_relative_links_to_absolute(self):
        # relative URLs are bad, b/c the text may be getting fetched to be
        # rendered in some other context. so they should get absolutized
        text_in = """<a href="image.jpg">image</a>"""
        text_out = """<a href="http://nohost/plone/image.jpg">image</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uid_plus_subpath(self):
        text_in = """<a href="resolveuid/%s/RSS">foo</a>""" % self.UID
        text_out = """<a href="http://nohost/plone/image.jpg/RSS">foo</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_unresolvable_uids(self):
        text_in = """<a href="resolveuid/foo">foo</a><a href="http://example.com/bar">bar</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolve_uids_non_AT_content(self):
        # UUIDs can be derefenced as long as they are in the UID index
        self._makeDummyContent()
        text_in = """<a href="resolveuid/foo">foo</a>"""
        text_out = """<a href="http://nohost/plone/foo">foo</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uids_fragment(self):
        self._makeDummyContent()
        self.parser = self._makeParser(resolve_uids=True,
                                       context=self.portal.foo)
        text_in = """<a href="#a">anchor</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolve_uids_in_image_maps(self):
        text_in = """<map id="the_map" name="the_map">
 <area alt="alpha" href="resolveuid/%s" coords="1,2,3,4" shape="rect" />
</map>""" % self.UID
        text_out = """<map id="the_map" name="the_map">
 <area alt="alpha" href="http://nohost/plone/image.jpg" coords="1,2,3,4" shape="rect" />
</map>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uids_handles_mailto(self):
        text_in = """<a href="mailto:foo@example.com">foo@example.com</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolve_uids_handles_tel(self):
        text_in = """<a href="tel:+1234567890">+12 345 67890</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolve_uids_handles_junk(self):
        text_in = """<a class="external-link" href="mailto&lt;foo@example.com&gt;">foo@example.com</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolve_uids_entities(self):
        text_in = """<a class="external-link" href="http://www.example.org/foo?a=1&amp;b=2">example.org</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolveuid_view(self):
        res = self.publish('/plone/resolveuid/%s' % self.UID)
        self.assertEqual(301, res.status)
        self.assertEqual('http://nohost/plone/image.jpg',
                         res.headers['location'])

    def test_resolveuid_view_bad_uuid(self):
        res = self.publish('/plone/resolveuid/BOGUS')
        self.assertEqual(404, res.status)

    def test_resolveuid_view_subpath(self):
        res = self.publish('/plone/resolveuid/%s/image_thumb' % self.UID)
        self.assertEqual(301, res.status)
        self.assertEqual('http://nohost/plone/image.jpg/image_thumb',
                         res.headers['location'])

    def test_resolveuid_view_querystring(self):
        res = self.publish('/plone/resolveuid/%s?qs' % self.UID)
        self.assertEqual(301, res.status)
        self.assertEqual('http://nohost/plone/image.jpg?qs',
                         res.headers['location'])

    def test_uuidToURL(self):
        from plone.outputfilters.browser.resolveuid import uuidToURL
        self.assertEqual('http://nohost/plone/image.jpg',
                         uuidToURL(self.UID))

    def test_uuidToObject(self):
        from plone.outputfilters.browser.resolveuid import uuidToObject
        self.assertTrue(self.portal['image.jpg'].aq_base
                        is uuidToObject(self.UID).aq_base)

    def test_uuidToURL_permission(self):
        from plone.outputfilters.browser.resolveuid import uuidToURL
        from plone.outputfilters.browser.resolveuid import uuidToObject
        self.portal.invokeFactory('Document', id='page', title='Page')
        page = self.portal['page']
        self.logout()
        self.assertEqual('http://nohost/plone/page',
                         uuidToURL(page.UID()))
        self.assertTrue(page.aq_base
                        is uuidToObject(page.UID()).aq_base)

    def test_image_captioning_in_news_item(self):
        # Create a news item with a relative unscaled image
        self.portal.invokeFactory('News Item', id='a-news-item', title='Title')
        news_item = self.portal['a-news-item']
        from plone.app.textfield.value import RichTextValue
        news_item.text = RichTextValue(
            '<p><img class="captioned" src="image.jpg"/></p>',
            'text/html', 'text/x-html-safe')
        news_item.setDescription("Description.")

        # Test captioning
        output = news_item.text.output
        self.assertRegexpMatches(output, r"""<p><dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/(.*?)\.jpeg" alt="Image" title="Image" height="331" width="500" /></dt>
 <dd class="image-caption" style="width:500px;">My caption</dd>
</dl></p>""")

    def test_image_captioning_absolutizes_uncaptioned_image(self):
        text_in = """<img src="/image.jpg" />"""
        text_out = """<img src="http://nohost/plone/image.jpg" alt="My caption" title="Image" />"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_absolute_path(self):
        text_in = """<img class="captioned" src="/image.jpg"/>"""
        text_out = """<dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/...jpeg" alt="Image" title="Image" height="331" width="500" /></dt>
 <dd class="image-caption" style="width:500px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_relative_path(self):
        text_in = """<img class="captioned" src="image.jpg"/>"""
        text_out = """<dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/...jpeg" alt="Image" title="Image" height="331" width="500" /></dt>
 <dd class="image-caption" style="width:500px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_relative_path_private_folder(self):
        # Images in a private folder may or may not still be renderable, but
        # traversal to them must not raise an error!
        self.loginAsPortalOwner()
        self.portal.invokeFactory('Folder', id='private',
            title='Private Folder')
        self.portal.private.invokeFactory('Image', id='image.jpg',
            title='Image')
        image = getattr(self.portal.private, 'image.jpg')
        image.setDescription('My private image caption')
        image.image = dummy_image()
        image.reindexObject()
        self.logout()

        text_in = """<img class="captioned" src="private/image.jpg"/>"""
        text_out = """<dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/private/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="331" width="500" /></dt>
 <dd class="image-caption" style="width:500px;">My private image caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_relative_path_scale(self):
        text_in = """<img class="captioned" src="image.jpg/@@images/image/thumb"/>"""
        text_out = """<dl style="width:128px;" class="captioned">
<dt><a rel="lightbox" href="/plone/image.jpg"><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="84" width="128" /></a></dt>
 <dd class="image-caption" style="width:128px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid(self):
        text_in = """<img class="captioned" src="resolveuid/%s"/>""" % self.UID
        text_out = """<dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="331" width="500" /></dt>
 <dd class="image-caption" style="width:500px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_scale(self):
        text_in = """<img class="captioned" src="resolveuid/%s/@@images/image/thumb"/>""" % self.UID
        text_out = """<dl style="width:128px;" class="captioned">
<dt><a rel="lightbox" href="/plone/image.jpg"><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="84" width="128" /></a></dt>
 <dd class="image-caption" style="width:128px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_new_scale(self):
        text_in = """<img class="captioned" src="resolveuid/%s/@@images/image/thumb"/>""" % self.UID
        text_out = """<dl style="width:128px;" class="captioned">
<dt><a rel="lightbox" href="/plone/image.jpg"><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="84" width="128" /></a></dt>
 <dd class="image-caption" style="width:128px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_new_scale_plone_namedfile(self):
        if not HAS_NAMEDFILE:
            return
        self._makeDummyContent()
        text_in = """<img class="captioned" src="resolveuid/foo2/@@images/image/thumb"/>"""
        text_out = """<img src="http://nohost/plone/foo2/@@images/....jpeg" alt="foo2" class="captioned" title="foo2" />"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_no_scale(self):
        text_in = """<img class="captioned" src="resolveuid/%s/@@images/image"/>""" % self.UID
        text_out = """<dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="331" width="500" /></dt>
<dd class="image-caption" style="width:500px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_no_scale_plone_namedfile(self):
        if not HAS_NAMEDFILE:
            return
        self._makeDummyContent()
        text_in = """<img class="captioned" src="resolveuid/foo2/@@images/image"/>"""
        text_out = """<img src="http://nohost/plone/foo2/@@images/....jpeg" alt="foo2" class="captioned" title="foo2" />"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_bad_uid(self):
        text_in = """<img src="resolveuid/notauid" width="120" height="144" start="fileopen" alt="Duncan's picture" class="image-left captioned" loop="1" />"""
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_unknown_scale(self):
        text_in = """<img src="resolveuid/%s/madeup" />""" % self.UID
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_unknown_scale_images_view(self):
        text_in = """<img src="resolveuid/%s/@@images/image/madeup" />""" % self.UID
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_external_url(self):
        text_in = """<img src="http://example.com/foo" class="captioned" />"""
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_preserves_custom_attributes(self):
        text_in = """<img class="captioned" width="42" height="42" foo="bar" src="image.jpg"/>"""
        text_out = """<dl style="width:42px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="42" width="42" foo="bar" /></dt>
 <dd class="image-caption" style="width:42px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_handles_unquoted_attributes(self):
        text_in = """<img class=captioned height=144 alt="picture alt text" src="resolveuid/%s" width=120 />""" % self.UID
        text_out = """<dl style="width:120px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="picture alt text" title="Image" height="144" width="120" /></dt>
 <dd class="image-caption" style="width:120px;">My caption</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_preserves_existing_links(self):
        text_in = """<a href="/xyzzy" class="link"><img class="image-left captioned" src="image.jpg/@@images/image/thumb"/></a>"""
        text_out = """<a href="/xyzzy" class="link"><dl style="width:128px;" class="image-left captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/....jpeg" alt="Image" title="Image" height="84" width="128" /></dt>
 <dd class="image-caption" style="width:128px;">My caption</dd>
</dl>
</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_handles_non_ascii(self):
        self.portal['image.jpg'].setTitle(u'Kupu Test Image \xe5\xe4\xf6')
        self.portal['image.jpg'].setDescription(u'Kupu Test Image \xe5\xe4\xf6')
        text_in = """<img class="captioned" src="image.jpg"/>"""
        text_out = """<dl style="width:500px;" class="captioned">
<dt><img src="http://nohost/plone/image.jpg/@@images/...jpeg" alt="Kupu Test Image \xc3\xa5\xc3\xa4\xc3\xb6" title="Kupu Test Image \xc3\xa5\xc3\xa4\xc3\xb6" height="331" width="500" /></dt>
 <dd class="image-caption" style="width:500px;">Kupu Test Image \xc3\xa5\xc3\xa4\xc3\xb6</dd>
</dl>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uids_with_bigU(self):
        text = """<a href="resolveUid/%s">foo</a>""" % self.UID
        res = self.parser(text)
        self.assertTrue('href="http://nohost/plone/image.jpg"' in str(res))

    def test_singleton_elements(self):
        self._assertTransformsTo('<hr/>\r\n<p>foo</p><br/>', '<hr />\r\n<p>foo</p><br />')

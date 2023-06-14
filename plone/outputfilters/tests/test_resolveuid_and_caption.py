from doctest import _ellipsis_match
from doctest import OutputChecker
from doctest import REPORT_NDIFF
from os.path import abspath
from os.path import dirname
from os.path import join
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing.bbb import PloneTestCase
from plone.namedfile.file import NamedBlobImage
from plone.namedfile.file import NamedImage
from plone.namedfile.tests.test_scaling import DummyContent as NFDummyContent
from plone.outputfilters.filters.resolveuid_and_caption import (  # noqa
    ResolveUIDAndCaptionFilter,
)
from plone.outputfilters.testing import PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING
from Products.PortalTransforms.tests.utils import normalize_html

import warnings


PREFIX = abspath(dirname(__file__))


def dummy_image():
    filename = join(PREFIX, "image.jpg")
    data = None
    with open(filename, "rb") as fd:
        data = fd.read()
        fd.close()
    return NamedBlobImage(data=data, filename=filename)


class ResolveUIDAndCaptionFilterIntegrationTestCase(PloneTestCase):
    layer = PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING

    image_id = "image.jpg"

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
                return "foo"

            allowedRolesAndUsers = ("Anonymous",)

        class DummyContent2(NFDummyContent):
            id = __name__ = "foo2"
            title = "Schönes Bild"

            def UID(self):
                return "foo2"

        dummy = DummyContent("foo")
        self.portal._setObject("foo", dummy)
        self.portal.portal_catalog.catalog_object(self.portal.foo)

        dummy2 = DummyContent2("foo2")
        with open(join(PREFIX, self.image_id), "rb") as fd:
            data = fd.read()
            fd.close()
        dummy2.image = NamedImage(data, "image/jpeg", "image.jpeg")
        self.portal._setObject("foo2", dummy2)
        self.portal.portal_catalog.catalog_object(self.portal.foo2)

    def _assertTransformsTo(self, input, expected, parsing=True):
        # compare two chunks of HTML ignoring whitespace differences,
        # and with a useful diff on failure
        if parsing:
            out = self.parser(input)
        else:
            out = input
        normalized_out = normalize_html(out)
        normalized_expected = normalize_html(expected)
        # print("e: {}".format(normalized_expected))
        # print("o: {}".format(normalized_out))
        try:
            self.assertTrue(_ellipsis_match(normalized_expected, normalized_out))
        except AssertionError:

            class wrapper:
                want = expected

            raise AssertionError(
                self.outputchecker.output_difference(wrapper, out, REPORT_NDIFF)
            )

    def afterSetUp(self):
        # create an image and record its UID
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        if self.image_id not in self.portal:
            self.portal.invokeFactory("Image", id=self.image_id, title="Image")
        image = self.portal[self.image_id]
        image.setDescription("My caption")
        image.image = dummy_image()
        image.reindexObject()
        self.UID = image.UID()
        self.parser = self._makeParser(captioned_images=True, resolve_uids=True)
        assert self.parser.is_enabled()

        self.outputchecker = OutputChecker()

    def beforeTearDown(self):
        self.login()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        del self.portal[self.image_id]

    def test_parsing_minimal(self):
        text = "<div>Some simple text.</div>"
        res = self.parser(text)
        self.assertEqual(text, str(res))

    def test_parsing_long_doc(self):
        text = """<div class="hero">
<h1>Welcome!</h1>
<p><a href="https://plone.com" class="btn btn-primary" target="_blank" rel="noopener">Learn more about Plone</a></p>
</div>
<p class="discreet">If you're seeing this instead of the web site you were expecting, the owner of this web site has just installed Plone. Do not contact the Plone Team or the Plone support channels about this.</p>
<p class="discreet"><img class="image-richtext image-inline image-size-small" src="resolveuid/{uid}/@@images/image/preview" alt="" data-linktype="image" data-srcset="small" data-scale="preview" data-val="{uid}" /></p>
<h2>Get started</h2>
<p>Before you start exploring your newly created Plone site, please do the following:</p>
<ol>
<li>Make sure you are logged in as an admin/manager user. <span class="discreet">(You should have a Site Setup entry in the user menu)</span></li>
<li><a href="@@mail-controlpanel" target="_blank" rel="noopener">Set up your mail server</a>. <span class="discreet">(Plone needs a valid SMTP server to verify users and send out password reminders)</span></li>
<li><a href="@@security-controlpanel" target="_blank" rel="noopener">Decide what security level you want on your site</a>. <span class="discreet">(Allow self registration, password policies, etc)</span></li>
</ol>
<h2>Get comfortable</h2>
<p>After that, we suggest you do one or more of the following:</p>
<ul>
<li>Find out <a href="https://plone.com/features/" class="link-plain" target="_blank" rel="noopener">What's new in Plone</a>.</li>
<li>Read the <a href="https://docs.plone.org" class="link-plain" target="_blank" rel="noopener">documentation</a>.</li>
<li>Follow a <a href="https://training.plone.org" class="link-plain" target="_blank" rel="noopener">training</a>.</li>
<li>Explore the <a href="https://plone.org/download/add-ons" class="link-plain" target="_blank" rel="noopener">available add-ons</a> for Plone.</li>
<li>Read and/or subscribe to the <a href="https://plone.org/support" class="link-plain" target="_blank" rel="noopener">support channels</a>.</li>
<li>Find out <a href="https://plone.com/success-stories/" class="link-plain" target="_blank" rel="noopener">how others are using Plone</a>.</li>
</ul>
<p><img class="image-richtext image-left image-size-medium captioned zoomable" src="resolveuid/{uid}/@@images/image/larger" alt="" data-linktype="image" data-srcset="medium" data-scale="larger" data-val="{uid}" /></p>
<h2>Make it your own</h2>
<p>Plone has a lot of different settings that can be used to make it do what you want it to. Some examples:</p>
<ul>
<li>Try out a different theme, either pick from <a href="@@theming-controlpanel" target="_blank" rel="noopener">the included ones</a>, or one of the <a href="https://plone.org/download/add-ons" class="link-plain" target="_blank" rel="noopener">available themes from plone.org</a>. <span class="discreet">(Make sure the theme is compatible with the version of Plone you are currently using)</span></li>
<li><a href="@@content-controlpanel" target="_blank" rel="noopener"> Decide what kind of workflow you want in your site.</a> <span class="discreet">(The default is typical for a public web site; if you want to use Plone as a closed intranet or extranet, you can choose a different workflow.)</span></li>
<li>By default, Plone uses a visual editor for content. <span class="discreet">(If you prefer text-based syntax and/or wiki syntax, you can change this in the <a href="@@markup-controlpanel" target="_blank" rel="noopener">markup control panel</a>)</span></li>
<li>…and many more settings are available in the <a href="@@overview-controlpanel" target="_blank" rel="noopener">Site Setup</a>.</li>
</ul>
<h2>Tell us how you use it</h2>
<p>Are you doing something interesting with Plone? Big site deployments, interesting use cases? Do you have a company that delivers Plone-based solutions?</p>
<ul>
<li>Add your company as a <a href="https://plone.com/providers/" class="link-plain" target="_blank" rel="noopener">Plone provider</a>.</li>
<li>Add a <a href="https://plone.com/success-stories/" class="link-plain" target="_blank" rel="noopener">success story</a> describing your deployed project and customer.</li>
</ul>
<h2>Find out more about Plone</h2>
<p>Plone is a powerful content management system built on a rock-solid application stack written using the Python programming language. More about these technologies:</p>
<ul>
<li>The <a href="https://plone.com" class="link-plain" target="_blank" rel="noopener">Plone open source Content Management System</a> web site for evaluators and decision makers.</li>
<li>The <a href="https://plone.org" class="link-plain" target="_blank" rel="noopener">Plone community </a> web site for developers.</li>
<li>The <a href="https://www.python.org" class="link-plain" target="_blank" rel="noopener">Python programming language</a> web site.</li>
</ul>
<h2><img class="image-richtext image-inline image-size-large" src="resolveuid/{uid}/@@images/image/huge" alt="" data-linktype="image" data-srcset="large" data-scale="huge" data-val="{uid}" /></h2>
<h2>Support the Plone Foundation</h2>
<p>Plone is made possible only through the efforts of thousands of dedicated individuals and hundreds of companies. The Plone Foundation:</p>
<ul>
<li>…protects and promotes Plone.</li>
<li>…is a registered 501(c)(3) charitable organization.</li>
<li>…donations are tax-deductible.</li>
<li><a href="https://plone.org/sponsors/be-a-hero" target="_blank" rel="noopener">Support the Foundation and help make Plone better!</a></li>
</ul>
<p>Thanks for using our product; we hope you like it!</p>
<p>—The Plone Team</p>
        """.format(
            uid=self.UID
        )
        import time

        startTime = time.time()
        res = self.parser(text)
        executionTime = time.time() - startTime
        print(f"\n\nresolve_uid_and_caption parsing time: {executionTime}\n")
        self.assertTrue(res)

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
    <a class="internal-link" href="resolveuid/{}">Some link</a>
    <a class="internal-link" href="resolveuid/{}#named-anchor">Some anchored link</a>
  </body>
</html>""".format(
            self.UID,
            self.UID,
        )
        res = str(self.parser(text))
        self.assertIn('href="http://nohost/plone/image.jpg"', res)
        self.assertIn('href="http://nohost/plone/image.jpg#named-anchor"', res)

    def test_resolve_uids_relative_link(self):
        text_in = """<a href="../resolveuid/%s">foo</a>""" % self.UID
        text_out = """<a href="http://nohost/plone/image.jpg">foo</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uids_abs_path(self):
        text_in = """<a href="/resolveuid/%s">foo</a>""" % self.UID
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
        # UUIDs can be dereferenced as long as they are in the UID index
        self._makeDummyContent()
        text_in = """<a href="resolveuid/foo">foo</a>"""
        text_out = """<a href="http://nohost/plone/foo">foo</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uids_fragment(self):
        self._makeDummyContent()
        self.parser = self._makeParser(resolve_uids=True, context=self.portal.foo)
        text_in = """<a href="#a">anchor</a>"""
        self._assertTransformsTo(text_in, text_in)

    def test_resolve_uids_in_image_maps(self):
        text_in = (
            """<map id="the_map" name="the_map">
<area alt="alpha" href="resolveuid/%s" coords="1,2,3,4" shape="rect" />
</map>"""
            % self.UID
        )
        text_out = """<map id="the_map" name="the_map">
<area alt="alpha" coords="1,2,3,4" href="http://nohost/plone/image.jpg" shape="rect"/>
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
        res = self.publish("/plone/resolveuid/%s" % self.UID)
        self.assertEqual(301, res.status)
        self.assertEqual("http://nohost/plone/image.jpg", res.headers["location"])

    def test_resolveuid_view_bad_uuid(self):
        res = self.publish("/plone/resolveuid/BOGUS")
        self.assertEqual(404, res.status)

    def test_resolveuid_view_missing_uuid(self):
        res = self.publish("/plone/resolveuid")
        self.assertEqual(404, res.status)

    def test_resolveuid_view_subpath(self):
        res = self.publish("/plone/resolveuid/%s/image_thumb" % self.UID)
        self.assertEqual(301, res.status)
        self.assertEqual(
            "http://nohost/plone/image.jpg/image_thumb", res.headers["location"]
        )

    def test_resolveuid_view_querystring(self):
        res = self.publish("/plone/resolveuid/%s?qs" % self.UID)
        self.assertEqual(301, res.status)
        self.assertEqual("http://nohost/plone/image.jpg?qs", res.headers["location"])

    def test_uuidToURL(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from plone.outputfilters.browser.resolveuid import uuidToURL

            self.assertEqual("http://nohost/plone/image.jpg", uuidToURL(self.UID))

    def test_uuidToObject(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from plone.outputfilters.browser.resolveuid import uuidToObject

            self.assertTrue(
                self.portal["image.jpg"].aq_base is uuidToObject(self.UID).aq_base
            )

    def test_uuidToURL_permission(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from plone.outputfilters.browser.resolveuid import uuidToObject
            from plone.outputfilters.browser.resolveuid import uuidToURL

            self.portal.invokeFactory("Document", id="page", title="Page")
            page = self.portal["page"]
            self.logout()
            self.assertEqual("http://nohost/plone/page", uuidToURL(page.UID()))
            self.assertTrue(page.aq_base is uuidToObject(page.UID()).aq_base)

    def test_image_captioning_in_news_item(self):
        # Create a news item with a relative unscaled image
        self.portal.invokeFactory("News Item", id="a-news-item", title="Title")
        news_item = self.portal["a-news-item"]
        from plone.app.textfield.value import RichTextValue

        news_item.text = RichTextValue(
            '<span><img class="captioned" src="image.jpg"/></span>',
            "text/html",
            "text/html",
        )
        news_item.setDescription("Description.")
        # Test captioning
        output = news_item.text.output
        text_out = """<span><figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="500"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>
</span>"""
        self._assertTransformsTo(output, text_out)

    def test_image_captioning_absolutizes_uncaptioned_image(self):
        text_in = """<img src="/image.jpg" />"""
        text_out = """<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/....jpeg" title="Image" width="500"/>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_absolute_path(self):
        text_in = """<img class="captioned" src="/image.jpg"/>"""
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="500"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_relative_path(self):
        text_in = """<img class="captioned" src="image.jpg"/>"""
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="500"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_relative_path_private_folder(self):
        # Images in a private folder may or may not still be renderable, but
        # traversal to them must not raise an error!
        self.loginAsPortalOwner()
        self.portal.invokeFactory("Folder", id="private", title="Private Folder")
        self.portal.private.invokeFactory("Image", id="image.jpg", title="Image")
        image = getattr(self.portal.private, "image.jpg")
        image.setDescription("My private image caption")
        image.image = dummy_image()
        image.reindexObject()
        self.logout()

        text_in = """<img class="captioned" src="private/image.jpg"/>"""
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/private/image.jpg/@@images/...jpeg" title="Image" width="500"/>
<figcaption class="image-caption">My private image caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_relative_path_scale(self):
        text_in = """<img class="captioned" src="image.jpg/@@images/image/thumb"/>"""
        text_out = """<figure class="captioned">
<img alt="" height="..." src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="..."/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_bare(self):
        text_in = """<img class="captioned" src="resolveuid/%s"/>""" % self.UID
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="500"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_scale(self):
        text_in = (
            """<img class="captioned" src="resolveuid/%s/@@images/image/thumb"/>"""
            % self.UID
        )
        text_out = """<figure class="captioned">
<img alt="" height="..." src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="..."/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_new_scale(self):
        text_in = (
            """<img class="captioned" src="resolveuid/%s/@@images/image/thumb"/>"""
            % self.UID
        )
        text_out = """<figure class="captioned">
<img alt="" height="..." src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="..."/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_new_scale_plone_namedfile(self):
        self._makeDummyContent()
        text_in = (
            """<img class="captioned" src="resolveuid/foo2/@@images/image/thumb"/>"""
        )
        text_out = """<img alt="" class="captioned" height="84" src="http://nohost/plone/foo2/@@images/...jpeg" title="Schönes Bild" width="128"/>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_no_scale(self):
        text_in = (
            """<img class="captioned" src="resolveuid/%s/@@images/image"/>""" % self.UID
        )
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="500"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_with_srcset_and_src(self):
        text_in = (
            """<img class="captioned" src="resolveuid/%s/@@images/image" srcset="resolveuid/%s/@@images/image 480w,resolveuid/%s/@@images/image 360w"/>"""
            % (self.UID, self.UID, self.UID)
        )
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" srcset="http://nohost/plone/image.jpg/@@images/...jpeg 480w,http://nohost/plone/image.jpg/@@images/...jpeg 360w" title="Image" width="500"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_iframe_resolveuid(self):
        text_in = """<iframe src="resolveuid/%s"/>""" % self.UID
        text_out = """<iframe src="http://nohost/plone/image.jpg"></iframe>"""
        self._assertTransformsTo(text_in, text_out)

    def test_video_resolveuid(self):
        text_in = """<video src="resolveuid/%s"/>""" % self.UID
        text_out = """<video src="http://nohost/plone/image.jpg"></video>"""
        self._assertTransformsTo(text_in, text_out)

    def test_audio_resolveuid(self):
        text_in = """<audio src="resolveuid/%s"/>""" % self.UID
        text_out = """<audio src="http://nohost/plone/image.jpg"></audio>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_resolveuid_no_scale_plone_namedfile(self):
        self._makeDummyContent()
        text_in = """<img class="captioned" src="resolveuid/foo2/@@images/image"/>"""
        text_out = """<img alt="" class="captioned" height="331" src="http://nohost/plone/foo2/@@images/...jpeg" title="Schönes Bild" width="500"/>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_bad_uid(self):
        text_in = """<img alt="Duncan's picture" class="image-left captioned" height="144" loop="1" src="resolveuid/notauid" start="fileopen" width="120"/>"""
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_unknown_scale(self):
        text_in = """<img src="resolveuid/%s/madeup"/>""" % self.UID
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_unknown_scale_images_view(self):
        text_in = """<img src="resolveuid/%s/@@images/image/madeup"/>""" % self.UID
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_external_url(self):
        text_in = """<img class="captioned" src="http://example.com/foo"/>"""
        self._assertTransformsTo(text_in, text_in)

    def test_image_captioning_preserves_custom_attributes(self):
        text_in = """<img class="captioned" width="42" height="42" foo="bar" src="image.jpg"/>"""
        text_out = """<figure class="captioned">
<img alt="" foo="bar" height="42" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="42"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_handles_unquoted_attributes(self):
        text_in = (
            """<img class=captioned height=144 alt="picture alt text" src="resolveuid/%s" width=120 />"""
            % self.UID
        )
        text_out = """<figure class="captioned">
<img alt="picture alt text" height="144" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="120"/>
<figcaption class="image-caption">My caption</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_preserves_existing_links(self):
        text_in = """<a href="/xyzzy" class="link"><img class="image-left captioned" src="image.jpg/@@images/image/thumb"/></a>"""
        text_out = """<a class="link" href="/xyzzy"><figure class="image-left captioned">
<img alt="" height="..." src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Image" width="..."/>
<figcaption class="image-caption">My caption</figcaption>
</figure>
</a>"""
        self._assertTransformsTo(text_in, text_out)

    def test_image_captioning_handles_non_ascii(self):
        self.portal["image.jpg"].setTitle("Kupu Test Image \xe5\xe4\xf6")
        self.portal["image.jpg"].setDescription("Kupu Test Image \xe5\xe4\xf6")
        text_in = """<img class="captioned" src="image.jpg"/>"""
        text_out = """<figure class="captioned">
<img alt="" height="331" src="http://nohost/plone/image.jpg/@@images/...jpeg" title="Kupu Test Image \xe5\xe4\xf6" width="500"/>
<figcaption class="image-caption">Kupu Test Image \xe5\xe4\xf6</figcaption>
</figure>"""
        self._assertTransformsTo(text_in, text_out)

    def test_resolve_uids_with_bigU(self):
        text = """<a href="resolveUid/%s">foo</a>""" % self.UID
        res = self.parser(text)
        self.assertTrue('href="http://nohost/plone/image.jpg"' in str(res))

    def test_singleton_elements(self):
        self._assertTransformsTo("<hr/>\r\n<p>foo</p><br/>", "<hr/>\r\n<p>foo</p><br/>")

    def test_no_change_when_a_in_script(self):
        text_in = """<script>a='<a href="">test</a>';</script>"""
        self._assertTransformsTo(text_in, text_in)

    def test_no_change_when_img_in_script(self):
        text_in = """<script>a='<img src="image.jpg" />';</script>"""
        self._assertTransformsTo(text_in, text_in)

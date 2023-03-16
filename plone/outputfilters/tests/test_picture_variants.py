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
from plone.outputfilters.filters.picture_variants import PictureVariantsFilter
from plone.outputfilters.testing import PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING
from Products.PortalTransforms.tests.utils import normalize_html


PREFIX = abspath(dirname(__file__))


def dummy_image():
    filename = join(PREFIX, "image.jpg")
    data = None
    with open(filename, "rb") as fd:
        data = fd.read()
        fd.close()
    return NamedBlobImage(data=data, filename=filename)


class PictureVariantsFilterIntegrationTestCase(PloneTestCase):
    layer = PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING

    image_id = "image.jpg"

    def _makeParser(self, **kw):
        parser = PictureVariantsFilter(context=self.portal)
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

    def _assertTransformsTo(self, input, expected):
        # compare two chunks of HTML ignoring whitespace differences,
        # and with a useful diff on failure
        out = self.parser(input)
        normalized_out = normalize_html(out)
        normalized_expected = normalize_html(expected)
        # print("\n e: {}".format(expected))
        # print("\n o: {}".format(out))
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
        text = """<div>
 Some simple text.
</div>"""
        res = self.parser(text)
        self.assertEqual(text, str(res))

    def test_parsing_long_doc(self):
        text = """<h1>Welcome!</h1>
<p class="discreet">If you're seeing this instead of the web site you were expecting, the owner of this web site has
    just installed Plone. Do not contact the Plone Team or the Plone support channels about this.</p>
<p class="discreet"><img class="image-richtext image-inline image-size-small"
        src="resolveuid/{uid}/@@images/image/preview" alt="" data-linktype="image" data-picturevariant="small"
        data-scale="preview" data-val="{uid}" /></p>
<h2>Get started</h2>
<p>Before you start exploring your newly created Plone site, please do the following:</p>
<ol>
    <li>Make sure you are logged in as an admin/manager user. <span class="discreet">(You should have a Site Setup entry
            in the user menu)</span></li>
</ol>
<h2>Get comfortable</h2>
<p>After that, we suggest you do one or more of the following:</p>
<p><img class="image-richtext image-left image-size-medium captioned zoomable"
        src="resolveuid/{uid}/@@images/image/larger" alt="" data-linktype="image" data-picturevariant="medium"
        data-scale="larger" data-val="{uid}" /></p>
<h2>Make it your own</h2>
<p>Plone has a lot of different settings that can be used to make it do what you want it to. Some examples:</p>
<h2>Tell us how you use it</h2>
<p>Are you doing something interesting with Plone? Big site deployments, interesting use cases? Do you have a company
    that delivers Plone-based solutions?</p>
<h2>Find out more about Plone</h2>
<p class="discreet"><img class="image-richtext image-right image-size-large" src="resolveuid/{uid}/@@images/image/huge"
        alt="" data-linktype="image" data-picturevariant="large" data-scale="huge" data-val="{uid}" /></p>
<p>Plone is a powerful content management system built on a rock-solid application stack written using the Python
    programming language. More about these technologies:</p>
<h2><img class="image-richtext image-inline image-size-large" src="resolveuid/{uid}/@@images/image/huge" alt=""
        data-linktype="image" data-picturevariant="large" data-scale="huge" data-val="{uid}" /></h2>
<h2>Support the Plone Foundation</h2>
<p>Plone is made possible only through the efforts of thousands of dedicated individuals and hundreds of companies. The
    Plone Foundation:</p>
<ul>
    <li>…protects and promotes Plone.</li>
    <li>…is a registered 501(c)(3) charitable organization.</li>
    <li>…donations are tax-deductible.</li>
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
        print(f"\n\nimage srcset parsing time: {executionTime}\n")
        self.assertTrue(res)

        text_out = """<h1>Welcome!</h1>
<p class="discreet">If you're seeing this instead of the web site you were expecting, the owner of this web site has
    just installed Plone. Do not contact the Plone Team or the Plone support channels about this.</p>
<p class="discreet">
    <picture>
        <source
            srcset="resolveuid/{uid}/@@images/image/preview 400w, resolveuid/{uid}/@@images/image/large 800w, resolveuid/{uid}/@@images/image/larger 1000w"/>
        <img alt="" class="image-richtext image-inline image-size-small" data-linktype="image"
            data-picturevariant="small" data-scale="preview" data-val="{uid}" loading="lazy"
            src="resolveuid/{uid}/@@images/image/preview"/>
    </picture>
</p>
<h2>Get started</h2>
<p>Before you start exploring your newly created Plone site, please do the following:</p>
<ol>
    <li>Make sure you are logged in as an admin/manager user.<span class="discreet">(You should have a Site Setup entry
            in the user menu)</span></li>
</ol>
<h2>Get comfortable</h2>
<p>After that, we suggest you do one or more of the following:</p>
<p>
    <picture class="captioned">
        <source
            srcset="resolveuid/{uid}/@@images/image/teaser 600w, resolveuid/{uid}/@@images/image/preview 400w, resolveuid/{uid}/@@images/image/large 800w, resolveuid/{uid}/@@images/image/larger 1000w, resolveuid/{uid}/@@images/image/great 1200w"/>
        <img alt="" class="image-richtext image-left image-size-medium captioned zoomable" data-linktype="image"
            data-picturevariant="medium" data-scale="larger" data-val="{uid}" loading="lazy"
            src="resolveuid/{uid}/@@images/image/teaser"/>
    </picture>
</p>
<h2>Make it your own</h2>
<p>Plone has a lot of different settings that can be used to make it do what you want it to. Some examples:</p>
<h2>Tell us how you use it</h2>
<p>Are you doing something interesting with Plone? Big site deployments, interesting use cases? Do you have a company
    that delivers Plone-based solutions?</p>
<h2>Find out more about Plone</h2>
<p class="discreet">
    <picture>
        <source
            srcset="resolveuid/{uid}/@@images/image/larger 1000w, resolveuid/{uid}/@@images/image/preview 400w, resolveuid/{uid}/@@images/image/teaser 600w, resolveuid/{uid}/@@images/image/large 800w, resolveuid/{uid}/@@images/image/great 1200w, resolveuid/{uid}/@@images/image/huge 1600w"/>
        <img alt="" class="image-richtext image-right image-size-large" data-linktype="image"
            data-picturevariant="large" data-scale="huge" data-val="{uid}" loading="lazy"
            src="resolveuid/{uid}/@@images/image/larger"/>
    </picture>
</p>
<p>Plone is a powerful content management system built on a rock-solid application stack written using the Python
    programming language. More about these technologies:</p>
<h2>
    <picture>
        <source
            srcset="resolveuid/{uid}/@@images/image/larger 1000w, resolveuid/{uid}/@@images/image/preview 400w, resolveuid/{uid}/@@images/image/teaser 600w, resolveuid/{uid}/@@images/image/large 800w, resolveuid/{uid}/@@images/image/great 1200w, resolveuid/{uid}/@@images/image/huge 1600w"/>
        <img alt="" class="image-richtext image-inline image-size-large" data-linktype="image"
            data-picturevariant="large" data-scale="huge" data-val="{uid}" loading="lazy"
            src="resolveuid/{uid}/@@images/image/larger"/>
    </picture>
</h2>
<h2>Support the Plone Foundation</h2>
<p>Plone is made possible only through the efforts of thousands of dedicated individuals and hundreds of companies. The
    Plone Foundation:</p>
<ul>
    <li>…protects and promotes Plone.</li>
    <li>…is a registered 501(c)(3) charitable organization.</li>
    <li>…donations are tax-deductible.</li>
</ul>
<p>Thanks for using our product; we hope you like it!</p>
<p>—The Plone Team</p>
        """.format(
            uid=self.UID
        )
        self._assertTransformsTo(text, text_out)

    def test_parsing_with_nonexisting_srcset(self):
        text = """
<p><img class="image-richtext image-inline image-size-thumb" src="resolveuid/{uid}/@@images/image/thumb" alt="" data-linktype="image" data-picturevariant="thumb" data-scale="thumb" data-val="{uid}" /></p>
        """.format(
            uid=self.UID
        )
        res = self.parser(text)
        self.assertTrue(res)
        # verify that tag was not converted:
        self.assertTrue("data-picturevariant" in res)

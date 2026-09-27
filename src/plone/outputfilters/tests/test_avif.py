from bs4 import BeautifulSoup
from io import BytesIO
from os.path import dirname
from os.path import join
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedBlobImage
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from plone.outputfilters.testing import PLONE_OUTPUTFILTERS_INTEGRATION_TESTING
from zope.component import getAdapters

import PIL.features
import PIL.Image
import re
import unittest

STABLE_AVIF = re.compile(
    r"^http://nohost/plone/pic/@@images/image-\d+-[0-9a-f]{32}\.avif$"
)
STABLE_JPEG = re.compile(
    r"^http://nohost/plone/pic/@@images/image-\d+-[0-9a-f]{32}\.jpeg$"
)
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'


def image_data():
    with open(join(dirname(__file__), "image.jpg"), "rb") as fd:
        return fd.read()


def avif_data():
    out = BytesIO()
    PIL.Image.new("RGB", (640, 480), (30, 120, 200)).save(out, "AVIF")
    return out.getvalue()


def srcset_urls(source):
    return [candidate.split()[0] for candidate in source["srcset"].split(",")]


@unittest.skipUnless(PIL.features.check_module("avif"), "Pillow cannot encode AVIF")
class TestRichTextImagesOfferAvif(unittest.TestCase):
    layer = PLONE_OUTPUTFILTERS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Image", id="pic", title="Picture")
        self.image = self.portal.pic
        self.image.image = NamedBlobImage(data=image_data(), filename="image.jpg")
        self.portal.invokeFactory("Document", id="doc")

    def render(self, html):
        filters = [f for _, f in getAdapters((self.portal.doc, self.request), IFilter)]
        return BeautifulSoup(apply_filters(filters, html), "html.parser")

    def rich_text_image(self, variant="medium"):
        return (
            f'<p><img src="resolveuid/{self.image.UID()}/@@images/image/teaser"'
            f' data-picturevariant="{variant}" alt="" /></p>'
        )

    def test_avif_source_comes_first_with_stable_urls(self):
        soup = self.render(self.rich_text_image())
        avif, original = soup.find_all("source")
        self.assertEqual(avif["type"], "image/avif")
        self.assertIsNone(original.get("type"))
        self.assertEqual(avif["sizes"], original["sizes"])
        for url in srcset_urls(avif):
            self.assertRegex(url, STABLE_AVIF)
        for url in srcset_urls(original):
            self.assertRegex(url, STABLE_JPEG)
        self.assertRegex(soup.img["src"], STABLE_JPEG)

    def test_avif_source_urls_serve_avif(self):
        soup = self.render(self.rich_text_image())
        url = srcset_urls(soup.source)[0]
        images = self.image.restrictedTraverse("@@images")
        self.request["TraversalRequestNameStack"] = []
        scale = images.publishTraverse(self.request, url.rsplit("/", 1)[-1])
        self.assertEqual(scale.data.contentType, "image/avif")
        self.assertEqual(scale.index_html()[4:12], b"ftypavif")

    def test_resolveuid_resolves_avif_scale_names(self):
        html = (
            '<picture><source type="image/avif" '
            f'srcset="resolveuid/{self.image.UID()}/@@images/image/preview.avif 400w" />'
            f'<img src="resolveuid/{self.image.UID()}/@@images/image/preview" />'
            "</picture>"
        )
        soup = self.render(html)
        self.assertRegex(srcset_urls(soup.source)[0], STABLE_AVIF)

    def test_svg_images_get_no_avif_source(self):
        self.image.image = NamedBlobImage(data=SVG, filename="logo.svg")
        soup = self.render(self.rich_text_image())
        self.assertEqual(len(soup.find_all("source")), 1)
        self.assertNotIn(".avif", str(soup))

    def test_avif_upload_falls_back_to_jpeg(self):
        self.image.image = NamedBlobImage(data=avif_data(), filename="pic.avif")
        self.assertEqual(self.image.image.contentType, "image/avif")
        soup = self.render(self.rich_text_image())
        avif, fallback = soup.find_all("source")
        self.assertEqual(avif["type"], "image/avif")
        for url in srcset_urls(avif):
            self.assertRegex(url, STABLE_AVIF)
        for url in srcset_urls(fallback):
            self.assertRegex(url, STABLE_JPEG)
        self.assertRegex(soup.img["src"], STABLE_JPEG)
        images = self.image.restrictedTraverse("@@images")
        self.request["TraversalRequestNameStack"] = []
        scale = images.publishTraverse(self.request, soup.img["src"].rsplit("/", 1)[-1])
        self.assertEqual(scale.index_html()[:3], b"\xff\xd8\xff")

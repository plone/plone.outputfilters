from unittest import TestCase
from plone.outputfilters.tests.base import OutputFiltersTestCase
from plone.outputfilters.filters.resolveuid_and_caption import \
    ResolveUIDAndCaptionFilter

class ResolveUIDAndCaptionFilterUnitTestCase(TestCase):

    def test_parsing_preserves_newlines(self):
        # Test if it preserves newlines which should not be filtered out
        text = """<pre>This is line 1
This is line 2</pre>"""
        parser = ResolveUIDAndCaptionFilter()
        res = parser(text)
        self.assertTrue('\n' in str(res))

    def test_parsing_preserves_CDATA(self):
        # Test if it preserves CDATA sections, such as those TinyMCE puts into
        # script tags. The standard SGMLParser has a bug that will remove
        # these.
        text = """<p>hello</p>
<script type="text/javsacript">// <![CDATA[
alert(1);
// ]]></script>
<p>world</p>"""
        parser = ResolveUIDAndCaptionFilter()
        res = parser(text)
        self.assertEqual(str(res), text)


class ResolveUIDAndCaptionFilterIntegrationTestCase(OutputFiltersTestCase):

    def afterSetUp(self):
        # create an image and record its UID
        self.setRoles(['Manager'])
        from Products.CMFPlone.tests import dummy
        self.portal.invokeFactory('Image', id='image', title='Image', file=dummy.Image())
        image = getattr(self.portal, 'image')
        image.reindexObject()
        self.UID = image.UID()

    def test_resolve_uids_in_images(self):
        text = """<html>
  <head></head>
  <body>
    <img src="resolveuid/%s/image_thumb" class="image-left captioned" width="200" alt="My alt text" />
    <p><img src="/plone/image.jpg" class="image-right captioned" width="200" style="border-width:1px" /></p>
  </body>
</html>""" % self.UID
        parser = ResolveUIDAndCaptionFilter(context=self.portal)
        res = parser(text)
        # The UID reference should be converted to an absolute url
        self.failUnless('<img src="http://nohost/plone/image/image_thumb" alt="My alt text" class="image-left captioned" width="200" />' in str(res))

    def test_resolve_uids_in_links(self):
        text = """<html>
  <head></head>
  <body>
    <a class="internal-link" href="resolveuid/%s">Some link</a>
    <a class="internal-link" href="resolveuid/%s#named-anchor">Some anchored link</a>
  </body>
</html>""" % (self.UID, self.UID)
        parser = ResolveUIDAndCaptionFilter(context=self.portal)
        res = parser(text)
        self.assertTrue('href="http://nohost/plone/image"' in str(res))
        self.assertTrue('href="http://nohost/plone/image#named-anchor"' in str(res))

    def test_resolve_uids_non_AT_content(self):
        pass

    def test_image_captioning(self):
        pass

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ResolveUIDAndCaptionFilterUnitTestCase))
    suite.addTest(makeSuite(ResolveUIDAndCaptionFilterIntegrationTestCase))
    return suite

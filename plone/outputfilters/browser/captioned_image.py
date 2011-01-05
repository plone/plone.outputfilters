from zope.cachedescriptors.property import Lazy as lazy_property
from Products.Five import BrowserView


class CaptionedImageView(BrowserView):
    """Captioned image template.
    """

    @lazy_property
    def template(self):
        try:
            # BBB for kupu
            template = self.context.restrictedTraverse('kupu_captioned_image')
        except:
            template = self.index
        return template

    def __call__(self, **options):
        return self.template(**options)

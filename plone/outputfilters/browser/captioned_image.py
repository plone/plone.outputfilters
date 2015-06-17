from zope.cachedescriptors.property import Lazy as lazy_property
from Products.Five import BrowserView


class CaptionedImageView(BrowserView):
    """Captioned image template.
    """

    @lazy_property
    def template(self):
        return self.index

    def __call__(self, **options):
        return self.template(**options)

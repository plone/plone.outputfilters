import zope.deferredimport


zope.deferredimport.initialize()

zope.deferredimport.deprecated(
    "Please use from plone.app.layout.outputfilters.captioned_image import CaptionedImageView",
    CaptionedImageView="plone.app.layout:outputfilters.captioned_image.CaptionedImageView",
)
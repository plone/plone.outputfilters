from Products.MimetypesRegistry.MimeTypeItem import MimeTypeItem


class text_plone_outputfilters_html(MimeTypeItem):
    __name__ = "Plone Output Filters HTML"
    mimetypes = ("text/x-plone-outputfilters-html",)
    binary = 0

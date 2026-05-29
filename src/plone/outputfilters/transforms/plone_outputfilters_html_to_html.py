from Products.PortalTransforms.interfaces import ITransform
from zope.interface import implementer


@implementer(ITransform)
class plone_outputfilters_html_to_html:
    __name__ = "plone_outputfilters_html_to_html"
    inputs = ("text/x-plone-outputfilters-html",)
    output = "text/html"

    def __init__(self, name=None):
        self.config_metadata = {
            "inputs": ("list", "Inputs", "Input(s) MIME type. Change with care."),
        }
        if name:
            self.__name__ = name

    def name(self):
        return self.__name__

    def convert(self, orig, data, **kwargs):
        # We actually don't do anything in this transform, it is
        # needed to get back in the transformation policy chain
        text = orig
        data.setData(text)
        return data


# This needs to be here to avoid breaking existing instances
def register():
    return plone_outputfilters_html_to_html()

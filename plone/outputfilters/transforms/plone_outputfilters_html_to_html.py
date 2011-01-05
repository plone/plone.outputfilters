from zope.interface import implements

try:
    try:
        from Products.PortalTransforms.interfaces import ITransform
    except ImportError:
        from Products.PortalTransforms.z3.interfaces import ITransform
except ImportError:
    ITransform = None
from Products.PortalTransforms.interfaces import itransform


class plone_outputfilters_html_to_html:
    if ITransform is not None:
        implements(ITransform)
    __implements__ = itransform
    __name__ = "plone_outputfilters_html_to_html"
    inputs = ('text/x-plone-outputfilters-html',)
    output = "text/html"

    def __init__(self, name=None):
        self.config_metadata = {
            'inputs': ('list', 'Inputs',
                       'Input(s) MIME type. Change with care.'),
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

from zope.component import getAdapters
from zope.interface import implements
try:
    from zope.component.hooks import getSite
except ImportError:
    from zope.app.component.hooks import getSite

try:
    try:
        from Products.PortalTransforms.interfaces import ITransform
    except ImportError:
        from Products.PortalTransforms.z3.interfaces import ITransform
except ImportError:
    ITransform = None
from Products.PortalTransforms.interfaces import itransform


from plone.outputfilters.interfaces import IFilter
from plone.outputfilters import apply_filters


class html_to_plone_outputfilters_html:
    """ transform which applies output filters"""
    if ITransform is not None:
        implements(ITransform)
    __implements__ = itransform
    __name__ = "html_to_plone_outputfilters_html"
    inputs = ('text/html',)
    output = "text/x-plone-outputfilters-html"

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
        context = kwargs.get('context')
        request = getattr(getSite(), 'REQUEST', None)
        filters = [f for _, f in getAdapters((context, request), IFilter)]

        res = apply_filters(filters, orig)
        data.setData(res)
        return data


# This needs to be here to avoid breaking existing instances
def register():
    return html_to_plone_outputfilters_html()

import re
from zope.interface import implements
from plone.outputfilters.interfaces import IFilter


class EmDashAdder(object):
    implements(IFilter)
    order = 1000

    def __init__(self, context, request):
        pass

    def is_enabled(self):
        return True

    pattern = re.compile(r'--')

    def __call__(self, data):
        return self.pattern.sub('\xe2\x80\x94', data)

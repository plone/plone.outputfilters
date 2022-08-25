from plone.outputfilters.interfaces import IFilter
from zope.interface import implementer

import re


@implementer(IFilter)
class EmDashAdder:
    order = 1000

    def __init__(self, context, request):
        pass

    def is_enabled(self):
        return True

    pattern = re.compile(r"--")

    def __call__(self, data):
        return self.pattern.sub("—", data)

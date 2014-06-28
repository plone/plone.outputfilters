Adding a custom filter
======================

As an example, the following filter replaces all doubled hyphens ("--") with em
dashes ("-"). (Don't use the example verbatim, because it doesn't parse HTML to
apply itself only to text nodes, so will mangle HTML comments.)

A filter is a callable which accepts a UTF-8-encoded HTML string as input, and
returns a modified UTF-8-encoded HTML string. A return value of ``None`` may be
used to indicate that the input should not be modified.

Example::

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

The ``order`` attribute may be used to affect the order in which filters are
applied (higher values run later). The is_enabled method should return a boolean
indicating whether the filter should be applied.

Filters are registered in ZCML as a named multi-adapter of the context and
request to IFilter.

 >>> from Zope2.App import zcml
 >>> import Products.Five
 >>> configure = """
 ... <configure
 ...     xmlns="http://namespaces.zope.org/zope">
 ...
 ...   <adapter
 ...     name="em_dash_adder"
 ...     provides="plone.outputfilters.interfaces.IFilter"
 ...     for="* *"
 ...     factory="plone.outputfilters.filters.example.EmDashAdder"
 ...     />
 ...
 ... </configure>
 ... """
 >>> zcml.load_config("configure.zcml", Products.Five)
 >>> zcml.load_string(configure)

Now when text is transformed from text/html to text/x-html-safe, the filter will
be applied.

 >>> app = layer['app']
 >>> portal = layer['portal']
 >>> str(portal.portal_transforms.convertTo('text/x-html-safe',
 ...     'test--test', mimetype='text/html', context=portal))
 'test\xe2\x80\x94test'


How it works
============

``plone.outputfilters`` hooks into the PortalTransforms machinery by installing:

1. a new mimetype ("text/x-plone-outputfilters-html")
2. a transform from text/html to text/x-plone-outputfilters-html
3. a null transform from text/x-plone-outputfilters-html back to text/html
4. a "transform policy" for the text/x-html-safe mimetype, which says that text
   being transformed to text/x-html-safe must first be transformed to
   text/x-plone-outputfilters-html

The filter adapters are looked up and applied during the execution of the
transform from step #2.

This should be considered an implementation detail and may change at some point
in the future.


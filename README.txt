plone.outputfilters
===================

``plone.outputfilters`` provides a framework for registering filters that
get applied to text as it is rendered.

By default, these filters are wired up to occur when text is transformed from
the text/html mimetype to the text/x-html-safe mimetype via the
PortalTransforms machinery.

With both Archetypes TextFields and the RichText field of
``plone.app.textfield``, this transform is typically applied when the field
value is first accessed. The result of the transform is then cached in a
volatile attribute for an hour or until the value is replaced.


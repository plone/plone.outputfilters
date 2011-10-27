Introduction
============

``plone.outputfilters`` provides a framework for registering filters that
get applied to text as it is rendered.

By default, these filters are wired up to occur when text is transformed from
the text/html mimetype to the text/x-html-safe mimetype via the
PortalTransforms machinery.

With both Archetypes TextFields and the RichText field of
``plone.app.textfield``, this transform is typically applied when the field
value is first accessed. The result of the transform is then cached in a
volatile attribute for an hour or until the value is replaced.


Included Filters
================

A default filter is included which provides the following features:

* Resolving UID-based links
* Adding captions to images

(These are implemented as one filter to avoid the overhead of parsing the HTML
twice.)

These features used to be provided by similar transforms in both Products.kupu
and Products.TinyMCE.  New releases of these editors are being prepared which
depend on the transform in plone.outputfilters, so that bugs don't need to be
fixed in multiple places.


Resolving UID-based links
-------------------------

Internal links may be inserted with a UID reference rather than the real path
of the item being linked.  For example, a link might look like this::

 <a href="resolveuid/6992f1f6-ae36-11df-9adf-001ec2a8cdf1">

Such URLs can be resolved by the ``resolveuid`` view, which resolves the UID to
an object and then redirects to its URL. However, resolving links in this way
requires an extra request after the redirect. The resolveuid filter avoids that
by replacing such URLs with the object's actual full absolute URL as the link
is rendered.

UIDs are resolved using ``plone.app.uuid.utils.uuidToURL``, with a fallback to
the Archetypes UID catalog for backwards compatibility. LinguaPlone translations
are supported when LinguaPlone is present.

The resolveuid filter is enabled if there is at least one
``plone.outputfilters.filters.resolveuid_and_caption.IResolveUidsEnabler``
utility whose ``available`` property returns ``True``.  This mechanism exists
for compatibility with TinyMCE and kupu, which both provide their own control
panel setting to enable the link-by-uid feature.


Image captioning
----------------

Image tags with the "captioned" class and a ``src`` attribute that resolves to
an image object within the site will be wrapped in a definition list (DL) tag
which includes a caption based on the value of the image's ``description``
field, if any.

For example, this image tag::

 <img src="path/to/image" class="captioned"/>

might be transformed into::

  <dl class="captioned">
   <dt><img src="path/to/image"/></dt>
   <dd class="image-caption">Caption text</dd>
  </dl>

assuming the image found at "path/to/image" has the description "Caption text".

The captioning filter is enabled if there is at least one
``plone.outputfilters.filters.resolveuid_and_caption.IImageCaptioningEnabler``
utility whose ``available`` property returns ``True``.  This mechanism exists
for compatibility with TinyMCE and kupu, which both provide their own control
panel setting to enable the captioning feature.

The captioned version of an image is rendered using the
``@@plone.outputfilters_captioned_image`` view, which may be overridden to
customize the caption.  This view is passed the following kwargs:

class
  The CSS class on the image.
originalwidth
  The ``width`` attribute of the image tag.
originalalt
  The ``alt`` attribute of the image tag.
url_path
  The path of the image, relative to the site root.
caption
  The image's description.
image
  The (possibly scaled) image object.
fullimage
  The original unscaled image object.
tag
  A full HTML tag which displays the image.
isfullsize
  True if ``image`` is ``fullimage``.
width
  The width of ``image``.


Adding a custom filter
======================

As an example, the following filter replaces all doubled hyphens ("--") with em
dashes ("—"). (Don't use the example verbatim, because it doesn't parse HTML to
apply itself only to text nodes, so will mangle HTML comments.)

A filter is a callable which accepts a UTF-8-encoded HTML string as input, and
returns a modified UTF-8-encoded HTML string. A return value of ``None`` may be
used to indicate that the input should not be modified.

 .. include:: plone/outputfilters/filters/example.py
    :literal:

The ``order`` attribute may be used to affect the order in which filters are
applied (higher values run later). The is_enabled method should return a boolean
indicating whether the filter should be applied.

Filters are registered in ZCML as a named multi-adapter of the context and
request to IFilter.

 >>> from Products.Five.zcml import load_string
 >>> load_string("""
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
 ... """)

Now when text is transformed from text/html to text/x-html-safe, the filter will
be applied.

 >>> str(self.portal.portal_transforms.convertTo('text/x-html-safe',
 ...     'test--test', mimetype='text/html', context=self.portal))
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


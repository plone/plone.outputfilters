Changelog
=========

2.1.4 (2016-05-10)
------------------

Fixes:

- Explicitly exclude ``mailto:`` links from being UID-resolved.
  [thet]

- Fix test isolation problem.
  [thet]

2.1.3 (2016-03-07)
------------------

New:

- Added ``tel:`` to ignored link types.
  [julianhandl]


2.1.2 (2015-12-15)
------------------

Fixes:

- Fixed error when uid resolving if object got didn't have
  absolute_url method.
  [Gagaro]

2.1.1 (2015-11-25)
------------------

Fixes:

- Fixed case where unicode ends up getting used when resolving
  img tags and (un)restrictedTraverse doesn't work with unicode.
  [vangheem]


2.1 (2015-07-18)
----------------

- Remove kupu BBB code.
  [gforcada]


2.0 (2015-03-13)
----------------

- For full-size (non-scaled) plone.app.contenttypes images,
  preserve height/width specified in img tag attributes.
  [davisagli]

- Convert tests to plone.app.testing
  [tomgross]


1.14 (2014-04-22)
-----------------

- for plone 5, always resolveuids
  [vangheem]


1.13 (2014-04-13)
-----------------

- #12783 img tag referencing non existent scales leads to transform error
  [anthonygerrard]


1.12 (2014-01-27)
-----------------

- Nothing changed yet.


1.11.1 (2013-07-19)
-------------------

- Fix README rst.
  [gotcha]


1.11 (2013-07-19)
-----------------

- img unicode issue : fix resolve_image to avoid that it returns unicode
  [gotcha]

- handle possibility of img tag being unicode to prevent unicode errors
  [vangheem]


1.10 (2013-05-23)
-----------------

- Work around bug in SGMLParser to handle singleton tags correctly.
  [tom_gross]


1.9 (2013-04-06)
----------------

- If we have an image description it should go into the alt text of the img
  tag
  [ale-rt]


1.8 (2012-12-10)
----------------

- Fix packaging issue.
  [esteele]


1.7 (2012-12-09)
----------------

- When resolving images, only look upward for the full image if the
  image that was traversed is not a content item (i.e. is a scale).
  [davisagli, datakurre]

- Also convert "resolveUid/" links (big 'U') that FCKeditor used to create.
  [hacklschorsch]

- Also escape double quotes, fixes #13219
  [maartenkling]

1.6 (2012-08-16)
----------------

- Don't break if an @@images scale can't be resolved for some reason.
  [davisagli]


1.5 (2012-08-15)
----------------

- Restore compatibility with Plone 4.0 when plone.outputfilters is present.
  [davisagli]


1.4 (2012-08-04)
----------------

- Fix incompatibilities with plone.namedfile
  [do3cc]


1.3 (2012-05-25)
----------------

- Fixed testing error by moving the part of README.rst to
  plone/outputfilters/README.txt.
  [maurits]

- Small pep8 update
  [pbdiode]


1.2 - 2012-04-09
----------------

- Prevent transformation of links to anchors on the same page.
  [davisagli]

- Fixed undefined uuid variable in kupu_resolveuid_hook branch
  in resolveuid view.
  [vincentfretin]

- Make sure links to expired objects can still be resolved by the resolveuid view.
  [davisagli]

- alt/title attributes on img tags were not present if tinymce uid linking was not used
  [iElectric]

- When making relative URIs absolute, use the parent as the relative
  root when the context is not folderish.  Fixes an issue where
  relative URLs from Plone 3, for example, had the wrong URLs under
  Plone 4 when a default page was used for a folder.
  [rossp]

- Fixed testing error when packaged with a missing README.rst.
  [maurits]


1.1 - 2011-11-21
----------------

- Fixed resolving of protected objects for AT content
  [tom_gross]

- Fixed resolving of relative ../resolveuid/... links
  [tom_gross]

- Respect implementation differences in Python 2.4 and
  Python 2.6 sgmlparser
  [tom_gross]

- Fixed resolving of images in protected folders for captioning
  [mj]


1.0 - 2011-05-13
----------------

- Release 1.0 Final.
  [esteele]

- Add MANIFEST.in.
  [WouterVH]


1.0b5 - 2011-03-24
------------------

- Make captioning and linking work with new style image scales.
  [elro]

- General refactoring of link resolution.
  [elro]


1.0b4 - 2011-03-22
------------------

- Add alt and title tags to images.
  [elro]

- Get various image properties from the imaging view to work better with
  Dexterity.
  [elro]

- small fix so it is possible to create object without need of REQUEST or
  without need of mocking it.
  [garbas]


1.0b3 - 2011-02-24
------------------

- Resolve image paths beginning with a slash relative to the Plone site root.
  [davisagli]

- Support image captioning for new-style image scales using the @@images view.
  [davisagli]


1.0b2 - 2011-01-11
------------------

- Fix resolveuid so that uid resolution occurs after authentication.
  [elro]

- Please remember to run tests before checking in!
  [elro]

- Fix issue where resolving links with subpaths resulted in a reversed
  subpath.
  [elro]


1.0b1 - 2011-01-25
------------------

- Fix issue with resolving resolveuid links with subpaths. This fixes
  http://dev.plone.org/plone/ticket/11426
  [davisagli]


1.0a1 - 2011-01-03
------------------

- Initial implementation.
  [davisagli]

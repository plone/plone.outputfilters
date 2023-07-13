Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

5.0.4 (2023-07-13)
------------------

Bug fixes:


- Call registry once per filter rather than for each img tag.
  [gotcha] (less_call_to_registry)


Internal:


- Update configuration files.
  [plone devs] (7723aeaf)


5.0.3 (2023-06-16)
------------------

Bug fixes:


- Return a 404 Not Found response if the resolveuid view is called with no uuid. @davisagli (#43)


5.0.2 (2023-04-14)
------------------

Internal:


- Update configuration files.
  [plone devs] (535edb14)


5.0.1 (2023-03-21)
------------------

Internal:


- Update configuration files.
  [plone devs] (243ca9ec)


5.0.0 (2022-11-17)
------------------

Bug fixes:


- Use our new version of uuidToObject() from plone.app.uuid.utils
  [anirudhhkashyap] (#52)


5.0.0b3 (2022-09-30)
--------------------

Bug fixes:


- Do not return prettified soup after picture variants filter.
  This prevents adding unneeded newlines.
  [petschki] (#56)


5.0.0b2 (2022-09-10)
--------------------

Bug fixes:


- isort, black, pyupgrade, manual six removal. 
  [jensens] (#53)


5.0.0b1 (2022-06-23)
--------------------

New features:


- Add image_srcset output filter, to convert IMG tags into PICTURE tags with multiple source definitions as define in imaging control panel [MrTango] (#49)


4.1.0 (2022-02-23)
------------------

New features:


- Resolve UIDs in SRC= attribute of of SOURCE and IFRAME elements. (#47)


4.0.2 (2020-09-28)
------------------

Bug fixes:


- fix AttributeError: 'NoneType' object has no attribute 'unwrap' exception when a fullsize image is wrapped in an <a> tag. [flipmcf] (#39)
- Fixed deprecation warning for html_quote.
  [maurits] (#3130)


4.0.1 (2020-04-21)
------------------

Bug fixes:


- Minor packaging updates. (#1)


4.0.0 (2020-03-13)
------------------

Breaking changes:

- Change the image caption template to use ``<figure>`` and ``<figcaption>``.
  [thet]

New features:

- Add an ``ImageCaptioningEnabler`` utility which can be enabled via the portal registry setting ``plone.image_captioning``.
  [thet]

Bug fixes:

- Don't check for hard coded image size in test.
  [agitator]

- Fixed possible package install error with Python 3.6 when no system locale is set.
  See `coredev issue 642 <https://github.com/plone/buildout.coredev/issues/642#issuecomment-597008272>`_.
  [maurits]


3.1.2 (2019-03-21)
------------------

Bug fixes:

- fix UnicodeDecodeError in Python 2 when uid-linked image has
  non-ascii characters in title or description
  [petschki]


3.1.1 (2019-01-07)
------------------

Bug fixes:

- bugfix for KeyError caused by <a> elements without href attribute
  [ajung]


3.1.0 (2018-11-02)
------------------

New features:

- remove deprecated sgmllib and move to BeautifulSoup4
  [tobiasherp, petschki]


3.0.5 (2018-06-04)
------------------

Bug fixes:

- Allow resolving of links with absolute path and host
  [tomgross]

- Make plone.namedfile hard testing dependency
  [tomgross]


3.0.4 (2018-02-02)
------------------

Bug fixes:

- Add Python 2 / 3 compatibility
  [pbauer]


3.0.3 (2017-08-04)
------------------

Bug fixes:

- update test to reflect changes in PortalTransforms
  [MrTango]

3.0.2 (2017-07-03)
------------------

Bug fixes:

- Remove unittest2 dependency
  [kakshay21]

3.0.1 (2017-02-05)
------------------

Bug fixes:

- Do not transform a and img tags when inside script tag.
  [gotcha]


3.0.0 (2016-08-19)
------------------

Breaking changes:

- Give up support of PortalTransforms 1.x with old style interfaces.
  [jensens]

Bug fixes:

- Handle unicode errors in img attributes
  [vangheem]
- Cleanup: utf8-headers, isort, pep8
  [jensens]

- Use zope.interface decorator.
  [gforcada]


2.1.5 (2016-06-07)
------------------

Bug fixes:

- Make tests work with old and new safe HTML transform
  [tomgross]


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

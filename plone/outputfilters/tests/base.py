from Testing import ZopeTestCase as ztc

from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite

ptc.setupPloneSite(extension_profiles=['plone.outputfilters:default'])


class OutputFiltersTestCase(ptc.FunctionalTestCase):

    class layer(PloneSite):

        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            import plone.outputfilters
            ztc.installPackage(plone.outputfilters)
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass


class OutputFiltersDocTestCase(OutputFiltersTestCase):
    # workaround for bug where the default test loader finds a bogus
    # test case in a test case class if it was previously used by
    # a Zope doctest suite
    pass

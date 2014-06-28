from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from zope.configuration import xmlconfig
from Products.Five import fiveconfigure
from plone.testing import z2


class PloneOutputfilters(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.outputfilters
        xmlconfig.file(
            'configure.zcml',
            plone.outputfilters,
            context=configurationContext
        )
        # Install product and call its initialize() function
        fiveconfigure.debug_mode = True
        z2.installProduct(app, 'plone.outputfilters')
        fiveconfigure.debug_mode = False

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.outputfilters:default')


PLONE_OUTPUTFILTERS_FIXTURE = PloneOutputfilters()
PLONE_OUTPUTFILTERS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_OUTPUTFILTERS_FIXTURE,),
    name="PloneOutputfilters:Integration")
PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_OUTPUTFILTERS_FIXTURE,),
    name="PloneOutputfilters:Functional")

from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.outputfilters.filters.resolveuid_and_caption import (  # noqa
    IImageCaptioningEnabler,
)
from zope.interface import implementer

import zope.component


@implementer(IImageCaptioningEnabler)
class DummyImageCaptioningEnabler:
    available = True


class PloneOutputfilters(PloneSandboxLayer):
    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import plone.outputfilters

        self.loadZCML(package=plone.outputfilters)
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerUtility(
            DummyImageCaptioningEnabler(),
            IImageCaptioningEnabler,
            "outputfiltertest",
            event=False,
        )

    def tearDownZope(self, app):
        gsm = zope.component.getGlobalSiteManager()
        gsm.unregisterUtility(provided=IImageCaptioningEnabler, name="outputfiltertest")

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.outputfilters:default")


PLONE_OUTPUTFILTERS_FIXTURE = PloneOutputfilters()
PLONE_OUTPUTFILTERS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_OUTPUTFILTERS_FIXTURE,), name="PloneOutputfilters:Integration"
)
PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_OUTPUTFILTERS_FIXTURE,), name="PloneOutputfilters:Functional"
)

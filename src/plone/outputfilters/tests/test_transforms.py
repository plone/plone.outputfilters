from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.outputfilters.testing import PLONE_OUTPUTFILTERS_INTEGRATION_TESTING

import unittest


class TransformsTestCase(unittest.TestCase):
    layer = PLONE_OUTPUTFILTERS_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        from Products.PortalTransforms.interfaces import IPortalTransformsTool
        from zope.component import getUtility

        self.transforms = getUtility(IPortalTransformsTool)

    def test_instantiate_html_to_plone_outputfilters_html_transform(self):
        from plone.outputfilters.transforms.html_to_plone_outputfilters_html import (
            html_to_plone_outputfilters_html,
        )

        transform = html_to_plone_outputfilters_html(name="transform")
        self.assertEqual("transform", transform.name())

    def test_instantiate_plone_outputfilters_html_to_html_transform(self):
        from plone.outputfilters.transforms.plone_outputfilters_html_to_html import (
            plone_outputfilters_html_to_html,
        )

        transform = plone_outputfilters_html_to_html(name="transform")
        self.assertEqual("transform", transform.name())

    def test_transform_policy_installed(self):
        policies = self.transforms.listPolicies()
        policies = [
            mimetype
            for (mimetype, required) in policies
            if mimetype == "text/x-html-safe"
        ]
        self.assertEqual(1, len(policies))

    def test_uninstallation(self):
        from plone.outputfilters.setuphandlers import uninstall_mimetype_and_transforms

        uninstall_mimetype_and_transforms(self.portal)

        policies = self.transforms.listPolicies()
        policies = [
            mimetype
            for (mimetype, required) in policies
            if mimetype == "text/x-html-safe"
        ]
        self.assertEqual(0, len(policies))

        # make sure it doesn't break if trying to uninstall again
        uninstall_mimetype_and_transforms(self.portal)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

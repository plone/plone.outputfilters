import unittest
from Testing import ZopeTestCase as ztc
from plone.outputfilters.tests.base import OutputFiltersDocTestCase


def test_suite():
    return unittest.TestSuite([

        ztc.ZopeDocFileSuite(
           '../../README.rst', package='plone.outputfilters',
           test_class=OutputFiltersDocTestCase),

        ])

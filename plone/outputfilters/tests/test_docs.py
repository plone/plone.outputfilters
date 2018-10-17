# -*- coding: utf-8 -*-
from plone.outputfilters.testing import PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING
from plone.testing import layered

import doctest
import pprint
import six
import unittest

optionflags = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_ONLY_FIRST_FAILURE
)

if six.PY3:
    normal_testfiles = [
        '../README.rst'
    ]
else:
    normal_testfiles = [
        './README_py2.rst',
    ]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite(test,
                                     optionflags=optionflags,
                                     globs={'pprint': pprint.pprint,
                                            },
                                     ),
                layer=PLONE_OUTPUTFILTERS_FUNCTIONAL_TESTING)
        for test in normal_testfiles])
    return suite

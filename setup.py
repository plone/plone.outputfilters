# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os


version = '3.0.1'

setup(name='plone.outputfilters',
      version=version,
      description=("Transformations applied to HTML in "
                   "Plone text fields as they are rendered"),
      long_description=(
          open("README.rst").read() + "\n" +
          open(os.path.join("plone", "outputfilters",
                            "README.rst")).read() + "\n" +
          open("CHANGES.rst").read()),
      # Get more strings from
      # https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Framework :: Plone :: 5.0",
          "Framework :: Plone :: 5.1",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.7",
      ],
      keywords='plone transform filter uid caption',
      author='David Glick, Plone Foundation',
      author_email='davidglick@groundwire.org',
      url='http://github.com/plone/plone.outputfilters',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'Products.CMFCore',
          'Products.GenericSetup',
          'Products.MimetypesRegistry',
          'Products.PortalTransforms>=2.0a1',
          'setuptools',
          'unidecode',
      ],
      extras_require={
          'test': [
              'plone.app.contenttypes',
              'plone.app.testing',
              'plone.app.robotframework',
          ],
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )

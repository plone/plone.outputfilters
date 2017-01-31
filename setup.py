from setuptools import setup, find_packages
import os

version = '1.15.3'

setup(name='plone.outputfilters',
      version=version,
      description="Transformations applied to HTML in Plone text fields as they are rendered",
      long_description=(open("README.rst").read() + "\n" +
                        open(os.path.join("plone", "outputfilters",
                                          "README.txt")).read() + "\n" +
                        open("CHANGES.rst").read()),
      # Get more strings from
      # https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Framework :: Plone :: 4.1",
          "Framework :: Plone :: 4.2",
          "Framework :: Plone :: 4.3",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2.6",
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
          'setuptools',
          'Products.CMFCore',
          'Products.GenericSetup',
          'Products.MimetypesRegistry',
          'Products.PortalTransforms',
      ],
      extras_require={
          'test': ['Products.PloneTestCase'],
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )

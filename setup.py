from setuptools import setup, find_packages
import os

version = '2.1.4'

setup(name='plone.outputfilters',
      version=version,
      description=("Transformations applied to HTML in "
                   "Plone text fields as they are rendered"),
      long_description=(
          open("README.rst").read() + "\n" +
          open(os.path.join("plone", "outputfilters",
                            "README.txt")).read() + "\n" +
          open("CHANGES.rst").read()),
      # Get more strings from
      # https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          "Framework :: Plone",
          "Framework :: Plone :: 5.0",
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
          'setuptools',
          'Products.CMFCore',
          'Products.GenericSetup',
          'Products.MimetypesRegistry',
          'Products.PortalTransforms',
      ],
      extras_require={
          'test': [
              'plone.app.contenttypes',
              'plone.app.testing',
          ],
      },
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )

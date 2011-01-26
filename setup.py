from setuptools import setup, find_packages
import os

version = '1.0b1'

setup(name='plone.outputfilters',
      version=version,
      description="Transformations applied to HTML in Plone text fields as they are rendered",
      long_description=open(os.path.join('plone', 'outputfilters', "README.txt")).read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone transform filter uid caption',
      author='David Glick, Plone Foundation',
      author_email='davidglick@groundwire.org',
      url='http://svn.plone.org/svn/plone/plone.outputfilters/trunk',
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
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone
      """,
      )

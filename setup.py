from setuptools import find_packages
from setuptools import setup

import os


version = "5.0.4"


def read(filename):
    with open(filename) as myfile:
        try:
            return myfile.read()
        except UnicodeDecodeError:
            # Happens on one Jenkins node on Python 3.6,
            # so maybe it happens for users too.
            pass
    # Opening and reading as text failed, so retry opening as bytes.
    with open(filename, "rb") as myfile:
        contents = myfile.read()
        return contents.decode("utf-8")


long_description = "\n".join(
    [
        read("README.rst"),
        read(os.path.join("plone", "outputfilters", "README.rst")),
        read("CHANGES.rst"),
    ]
)

setup(
    name="plone.outputfilters",
    version=version,
    description=(
        "Transformations applied to HTML in " "Plone text fields as they are rendered"
    ),
    long_description=long_description,
    # Get more strings from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: Core",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="plone transform filter uid caption",
    author="David Glick, Plone Foundation",
    author_email="davidglick@groundwire.org",
    url="http://github.com/plone/plone.outputfilters",
    license="GPL",
    packages=find_packages(),
    namespace_packages=["plone"],
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "setuptools",
        "beautifulsoup4",
        "DocumentTemplate",
        "Products.GenericSetup",
        "Products.MimetypesRegistry",
        "Products.PortalTransforms>=2.0",
        "plone.app.uuid>=2.2.0",
        "plone.base",
        "plone.namedfile",
        "plone.registry",
        "plone.uuid",
        "zope.cachedescriptors",
    ],
    extras_require={
        "test": [
            "plone.app.contenttypes[test]",
            "plone.app.testing",
            "plone.app.textfield",
            "plone.namedfile",
            "plone.testing",
        ]
    },
    entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
)

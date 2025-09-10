from pathlib import Path
from setuptools import find_packages
from setuptools import setup


version = "5.0.5"

long_description = (
    f"{Path('README.rst').read_text()}\n"
    f"{(Path('src') / 'plone' / 'outputfilters' / 'README.rst').read_text()}\n"
    f"{Path('CHANGES.rst').read_text()}\n"
)

setup(
    name="plone.outputfilters",
    version=version,
    description=(
        "Transformations applied to HTML in Plone text fields as they are rendered"
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
    packages=find_packages("src"),
    namespace_packages=["plone"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "setuptools",
        "beautifulsoup4",
        "Products.GenericSetup",
        "Products.MimetypesRegistry",
        "Products.PortalTransforms>=2.0",
        "plone.app.uuid>=2.2.0",
        "plone.base",
        "plone.namedfile",
        "plone.registry",
        "plone.uuid",
        "Zope",
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

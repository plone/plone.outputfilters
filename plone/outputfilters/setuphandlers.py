from zope.component import getUtility
from Products.PortalTransforms.interfaces import IPortalTransformsTool
from Products.MimetypesRegistry.interfaces import IMimetypesRegistryTool

from plone.outputfilters.mimetype import text_plone_outputfilters_html
from plone.outputfilters.transforms.plone_outputfilters_html_to_html import \
    plone_outputfilters_html_to_html
from plone.outputfilters.transforms.html_to_plone_outputfilters_html import \
    html_to_plone_outputfilters_html


def register_mimetype(context, mimetype):
    mimetypes_registry = getUtility(IMimetypesRegistryTool)
    mimetypes_registry.register(mimetype())


def unregister_mimetype(context, mimetype):
    mimetypes_registry = getUtility(IMimetypesRegistryTool)
    mimetype_instance = mimetypes_registry.lookup(mimetype)
    if mimetype_instance:
        mimetypes_registry.unregister(mimetype_instance[0])


def register_transform(context, transform):
    transform_tool = getUtility(IPortalTransformsTool)
    transform = transform()
    transform_tool.registerTransform(transform)


def unregister_transform(context, transform):
    transform_tool = getUtility(IPortalTransformsTool)
    if hasattr(transform_tool, transform):
        transform_tool.unregisterTransform(transform)


def register_transform_policy(context, output_mimetype, required_transform):
    transform_tool = getUtility(IPortalTransformsTool)
    unregister_transform_policy(context, output_mimetype)
    transform_tool.manage_addPolicy(output_mimetype, [required_transform])


def unregister_transform_policy(context, output_mimetype):
    transform_tool = getUtility(IPortalTransformsTool)
    policies = [mimetype for (mimetype, required)
                in transform_tool.listPolicies()
                if mimetype == output_mimetype]
    if policies:
        # There is a policy, remove it!
        transform_tool.manage_delPolicies([output_mimetype])


def install_mimetype_and_transforms(context):
    """ register mimetype and transformations for captioned images """
    register_mimetype(context, text_plone_outputfilters_html)
    register_transform(context, plone_outputfilters_html_to_html)
    register_transform(context, html_to_plone_outputfilters_html)
    register_transform_policy(context, "text/x-html-safe",
                              "html_to_plone_outputfilters_html")


def uninstall_mimetype_and_transforms(context):
    """ unregister mimetype and transformations for captioned images """
    unregister_transform(context, "plone_outputfilters_html_to_html")
    unregister_transform(context, "html_to_plone_outputfilters_html")
    unregister_mimetype(context, 'text/x-plone-outputfilters-html')
    unregister_transform_policy(context, "text/x-html-safe")


def importVarious(context):
    if context.readDataFile('plone.outputfilters.txt') is None:
        return
    site = context.getSite()
    install_mimetype_and_transforms(site)

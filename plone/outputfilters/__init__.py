jbot_deprecations = {
    "plone.outputfilters.browser.captioned_image.pt": "plone.app.layout.browser.captioned_image.pt"
}


def apply_filters(filters, data):
    filters = sorted(filters, key=lambda x: x.order)
    for filter in filters:
        if filter.is_enabled():
            res = filter(data)
            if res is not None:
                data = res
    return data

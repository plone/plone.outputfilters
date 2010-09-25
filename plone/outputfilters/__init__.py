def apply_filters(filters, data):
    by_order = lambda x: x.order
    filters = sorted(filters, key=by_order)
    for filter in filters:
        if filter.is_enabled():
            res = filter(data)
            if res is not None:
                data = res
    return data

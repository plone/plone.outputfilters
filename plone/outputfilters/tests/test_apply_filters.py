import unittest

from plone.outputfilters import apply_filters


class DummyFilter(object):
    order = 500

    def is_enabled(self):
        return True

    called = []

    def __call__(self, data):
        self.__class__.called.append(self)
        return data


class FilterTestCase(unittest.TestCase):

    def setUp(self):
        DummyFilter.called = []

    def test_apply_filters(self):
        filters = [DummyFilter()]

        apply_filters(filters, '')
        self.assertEqual([filters[0]], DummyFilter.called)

    def test_apply_filters_ordering(self):
        filter1 = DummyFilter()
        filter2 = DummyFilter()
        filter2.order = 100
        filters = [filter1, filter2]

        apply_filters(filters, '')
        self.assertEqual([filters[1], filters[0]], DummyFilter.called)

    def test_apply_filters_checks_is_enabled(self):
        filter = DummyFilter()
        filter.is_enabled = lambda: False
        filters = [filter]

        apply_filters(filters, '')
        self.assertEqual([], DummyFilter.called)

    def test_apply_filters_handles_return_none(self):
        class DummyFilterReturningNone(DummyFilter):
            def __call__(self, data):
                return None
        filter = DummyFilterReturningNone()

        res = apply_filters([filter], '')
        self.assertEqual('', res)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

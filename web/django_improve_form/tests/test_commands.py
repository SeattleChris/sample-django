from django.test import TestCase  # , TransactionTestCase, Client, RequestFactory,
# from unittest import skip
# from django.core.management import call_command
# from .helper_admin import APP_NAME
from project.management.commands.urllist import Command as urllist
# import json
# from django.conf import settings
# from pprint import pprint

# urls = call_command('urllist', APP_NAME, only=i, long=True, data=True)
# Create your tests here.


class UrllistTests(TestCase):
    com = urllist()
    base_opts = {'sources': [], 'ignore': [], 'only': ['5'], 'not': [], 'add': [], 'cols': None, 'data': True, }
    base_opts.update({'long': True, 'sort': urllist.initial_sort, 'sub_cols': urllist.initial_sub_cols, })
    # 'long' and 'data' are False by default, but most of our tests use True for clarity sake.

    def test_get_col_names(self):
        """Confirm it processes correctly when the 'only' parameter has an integer value. """
        priorities = urllist.column_priority
        all_cols = urllist.all_columns
        max_value = len(priorities)
        opts = self.base_opts.copy()
        for i in range(1, max_value):
            expected = [ea for ea in all_cols if ea in priorities[:i]]
            opts['only'] = [str(i)]
            actual = self.com.get_col_names(opts)
            self.assertListEqual(expected, actual)

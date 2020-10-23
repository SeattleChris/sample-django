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

    def test_get_col_names_by_priority(self):
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

    def test_sub_rules_default(self):
        """The sub_rules are expected to include the defaults for default settings (long=False). """
        expected = [(*rule, urllist.initial_sub_cols) for rule in urllist.initial_sub_rules]
        opts = self.base_opts.copy()
        opts['long'] = False
        actual = self.com.get_sub_rules(opts)
        self.assertListEqual(expected, actual)

    def test_sub_rules_when_long(self):
        """The sub_rules are expected to be empty when 'long' is True and there are no added sub_rules. """
        expected = []
        opts = self.base_opts.copy()
        actual = self.com.get_sub_rules(opts)
        self.assertListEqual(expected, actual)

    def test_add_sub_rules_default(self):
        """The sub_rules are expected to include the defaults and added rules, on default columns. """
        expected = [(*rule, urllist.initial_sub_cols) for rule in urllist.initial_sub_rules]
        new_rules = [('dog', 'woof'), ('cat', 'meow')]
        expected += [(*rule, urllist.initial_sub_cols) for rule in new_rules]
        opts = self.base_opts.copy()
        opts['long'] = False
        opts['add'] = new_rules
        actual = self.com.get_sub_rules(opts)
        self.assertListEqual(expected, actual)

    def test_add_sub_rules_default_with_cols(self):
        """The sub_rules are expected to include the defaults on their columns, added on defined columns. """
        expected = [(*rule, urllist.initial_sub_cols) for rule in urllist.initial_sub_rules]
        new_rules = [('dog', 'woof'), ('cat', 'meow')]
        cols = ['pattern', 'args']
        expected += [(*rule, cols) for rule in new_rules]
        opts = self.base_opts.copy()
        opts['long'] = False
        opts['add'] = new_rules
        opts['cols'] = cols
        actual = self.com.get_sub_rules(opts)
        self.assertListEqual(expected, actual)

    def test_add_sub_rules_when_long_no_cols(self):
        """The sub_rules are expected to only include the added rules, on the default columns. """
        new_rules = [('dog', 'woof'), ('cat', 'meow')]
        expected = [(*rule, urllist.initial_sub_cols) for rule in new_rules]
        opts = self.base_opts.copy()
        opts['add'] = new_rules
        actual = self.com.get_sub_rules(opts)
        self.assertListEqual(expected, actual)

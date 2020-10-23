from django.test import TestCase  # , TransactionTestCase, Client, RequestFactory,
from unittest import skip
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

    def test_error_on_malformed_collect_urls(self):
        """The collect_urls method requires urls parameter to be a URLResolver, URLPattern, or None. """
        bad_input = 'This is not any kind of a django.urls resolver.'
        with self.assertRaises(ValueError):
            self.com.collect_urls(bad_input)

    @skip("Not Implemented")
    def test_get_url_data_when_all_urls_empty(self):
        """Returns an empty list if the urlpatterns are empty. """
        # override settings so the settings.ROOT_URLCONF will resolve in an empty list of urls.
        # urlconf_name is the dotted Python path to the module defining urlpatterns.
        # It may also be an object with an urlpatterns attribute
        # or urlpatterns itself.
        pass

    @skip("Not Implemented")
    def test_get_url_data_append_sources(self):
        """If sources parameter is not None, it will have 'source' appended to the list of this parameter value. """
        pass

    @skip("Not Implemented")
    def test_process_sub_rules(self):
        """If sub_rules parameter has a value for get_url_data, these rules should be processed for the results. """
        pass

    @skip("Not Implemented")
    def test_get_url_data_empty_result(self):
        """If the non-empty all_urls are filtered down to no results, it sends an empty list and not the title. """
        pass

    @skip("Not Implemented")
    def test_handle_when_not_data_response(self):
        """If 'data' is false, it should call data_to_string, write to stdout, and return 0. """
        pass

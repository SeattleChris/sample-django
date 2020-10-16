import re
import json
from django.core.management import BaseCommand
from django.urls import resolvers

EMPTY_VALUE = ["************* NO URLS FOUND *************"]


def collect_urls(urls=None, source=None, prefix=None):
    if urls is None:
        urls = resolvers.get_resolver()
    prefix = prefix or []
    if isinstance(urls, resolvers.URLResolver):
        name = urls.urlconf_name
        if isinstance(name, (list, tuple)):
            name = ''
        elif not isinstance(name, str):
            name = name.__name__
        source = urls.namespace or name.split('.')[0] or source
        res = []
        for x in urls.url_patterns:
            res += collect_urls(x, source=source,
                                prefix=prefix + [str(urls.pattern)])
        return res
    elif isinstance(urls, resolvers.URLPattern):
        pattern = prefix + [str(urls.pattern)]
        pattern = ''.join([ea for ea in pattern if ea])[1:]
        return [{'source': source,
                 'name': urls.name,
                 'pattern': pattern,
                 'lookup_str': urls.lookup_str,
                 'args': dict(urls.default_args)}]
    else:
        raise ValueError(repr(urls))


def make_columns(url, cols, lengths={}):
    if len(cols) == 1:
        columns = [v for k, v in url.items() if k in cols]
    else:
        columns = [('{:%d}' % lengths.get(k, len(v))).format(v) for k, v in url.items() if k in cols]
    return columns


def get_sub_rules(kwargs):
    sc = kwargs.get('sub_cols', [])
    sub_rules = [('^django.contrib', 'cb ', sc), ('^django_registration', 'd_reg ', sc), ('^django', '', sc)]
    if kwargs['long']:
        sub_rules = []
    add_rules = [(*rule, kwargs['cols'] or sc) for rule in kwargs['add']]
    sub_rules.extend(add_rules)
    return sub_rules


def get_col_names(kwargs):
    col_names = kwargs['only'] or ['source', 'name', 'pattern', 'lookup_str', 'args']
    return [ea for ea in col_names if ea not in kwargs['not']]


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('sources', nargs='*', type=str, default=[], metavar='source',
                            help='Only show url info from the namespace or module source(s) listed. Default: show all.')
        # Optional Named Arguments: Rows (modules) and Columns (info about the url setting).
        parser.add_argument('--ignore', nargs='*', default=[], help='List of sources to ignore.', metavar='source')
        parser.add_argument('--only', nargs='*', help='Only show the following columns. ', metavar='col')
        parser.add_argument('--not', nargs='*', default=[], help='Do NOT show the following columns.', metavar='col')
        parser.add_argument('--sort', nargs='*', default=['source', 'name'],  metavar='col',
                            help='Sort by, in order of priority, column(s) value. Default: source name. ',)
        # Optional Named Arguments: String substitutions for tighter view and readability.
        parser.add_argument('--long', '-l', action='store_true', help='Show full text: remove default substitutions.', )
        parser.add_argument('--sub-cols', nargs='*', action='store', default=['source', 'name', 'lookup_str'],
                            help='Columns to apply the default substitutions. ', metavar='col', )
        parser.add_argument('--add', '-a', nargs=2, default=[], action='append', metavar=('regex', 'value', ),
                            help='Add a substitution rule: regex, value.', )
        parser.add_argument('--cols', '-c', nargs='*', metavar='col',
                            help='Columns to apply added substitutions. If none given, defaults to sub-cols. ', )
        # Optional Named Argument: Flag for returning results when called within code instead of command line.
        parser.add_argument('--data', '-d', action='store_true', help='Return results usable in application code.', )

    def handle(self, *args, **kwargs):
        col_names = get_col_names(kwargs)
        sub_rules = get_sub_rules(kwargs)
        result = show_urls(kwargs['sources'], kwargs['ignore'], col_names, sort=kwargs['sort'], sub_rules=sub_rules)
        if kwargs['data']:
            if result == EMPTY_VALUE:
                result = []
            elif len(col_names) == 1:
                result = [ea.strip() for ea in result]
            else:
                result = result[2:]
            return json.dumps([ea.strip() for ea in result])
        else:
            self.stdout.write('\n'.join(result))
            return 0

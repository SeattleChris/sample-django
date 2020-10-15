import sys
import re
from django.core.management import BaseCommand
from django.urls import resolvers


def collect_urls(urls=None, namespace=None, prefix=None):
    if urls is None:
        urls = resolvers.get_resolver()
    prefix = prefix or []
    if isinstance(urls, resolvers.URLResolver):
        # sys.stdout.write("*************************** RESOLVER ************************** \n")
        name = urls.urlconf_name
        if isinstance(name, (list, tuple)):
            name = ''
        elif not isinstance(name, str):
            name = name.__name__
        namespace = urls.namespace or name.split('.')[0] or namespace
        res = []
        for x in urls.url_patterns:
            res += collect_urls(x, namespace=urls.namespace or namespace,
                                prefix=prefix + [str(urls.pattern)])
        return res
    elif isinstance(urls, resolvers.URLPattern):
        pattern = prefix + [str(urls.pattern)]
        pattern = ''.join([ea for ea in pattern if ea])[1:]
        # sys.stdout.write("*************************** URLPattern ************************** \n")
        return [{'namespace': namespace,
                 'name': urls.name,
                 'pattern': pattern,
                 'lookup_str': urls.lookup_str,
                 'args': dict(urls.default_args)}]
    else:
        raise ValueError(repr(urls))


def show_urls(sub_rules=None, sub_cols=None):
    all_urls = collect_urls()
    if not all_urls:
        sys.stdout.write("************* NO URLS FOUND *************")
        return
    title = {key: key for key in all_urls[0].keys()}
    all_urls.append(title)
    remove_idx = []
    max_lengths = {}
    for i, u in enumerate(all_urls):
        for col in ['name', 'args']:
            u[col] = str(u[col])
        if sub_rules and sub_cols:
            for col in sub_cols:
                val = u[col]
                for regex, new_str in sub_rules:
                    val = re.sub(regex, new_str, val)
                u[col] = val
        for k, v in list(u.items())[:-1]:  # no ending border, so last column width not needed.
            u[k] = v = v or ''
            # If it is known to be unimportant and too long, prepare it to be removed and don't compute column width.
            if (u['namespace'], u['name']) == ('admin', 'view_on_site'):
                remove_idx.append(i)
                continue
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))
    for row in reversed(remove_idx):
        all_urls.pop(row)
    title = all_urls.pop()
    bar = {key: '*' * max_lengths.get(key, 3) for key in title}
    title = [title, bar]
    all_urls = title + sorted(all_urls, key=lambda x: (x['namespace'], x['name']))
    for u in all_urls:
        sys.stdout.write(' | '.join(
            ('{:%d}' % max_lengths.get(k, len(v))).format(v)
            for k, v in u.items()) + '\n')


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('modules', nargs='*', type=str, default='all',
                            help='Only show these listed modules. Default: show all.')
        # Named (optional) arguments
        parser.add_argument('--ignore', nargs='*', help='List of modules to ignore.', metavar='module')
        parser.add_argument('--only', nargs='*', help='Show only listed column names. ', metavar='col')
        parser.add_argument('--not', nargs='*', help='Show all columns except those listed.', metavar='col')

        parser.add_argument('--long', '-l', action='store_true', help='Show full text: remove default substitutions.', )
        parser.add_argument('--sub-cols', nargs='*', action='store', default=['namespace', 'name', 'lookup_str'],
                            help='Columns for default substitutions. ', metavar='col', )
        parser.add_argument('--add', '-a', nargs=2, action='append', metavar=('regex', 'value', ),
                            help='Add a substitution rule: regex, value.', )
        parser.add_argument('--cols', '-c', nargs='*', help='Columns used for added substitutions.', metavar='col')

    # end def add_arguments

    def handle(self, *args, **kwargs):
        sys.stdout.write(str(args) + "\n")
        sys.stdout.write(str(kwargs) + "\n\n")
        sub_cols = kwargs.get('sub_cols', [])
        sub_rules = [('^django.contrib', 'cb '), ('^django_registration', 'd_reg '), ('^django', '')]
        if kwargs['long']:
            sub_rules = None
        show_urls(sub_rules=sub_rules, sub_cols=sub_cols)

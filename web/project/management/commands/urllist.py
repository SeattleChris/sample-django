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
    max_lengths = {}
    for u in all_urls:
        for k in ['name', 'args']:
            u[k] = str(u[k])
        for k in sub_cols:
            v = u[k]
            for a, b in sub_rules:
                v = re.sub(a, b, v)
            u[k] = v
        for k, v in list(u.items())[:-1]:  # no ending border, so last column width not needed.
            u[k] = v = v or ''
            # Skip app_list due to length (contains all app names)
            # if (u['namespace'], u['name'], k) == ('admin', 'app_list', 'pattern'):
            #     continue
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))
    bar = {key: '*' * max_lengths.get(key, 4) for key in title}
    all_urls = all_urls[-1:] + [bar] + sorted(all_urls[:-1], key=lambda x: (x['namespace'], x['name']))
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
        parser.add_argument('--ignore', nargs='*', action='store', help='List of modules to ignore.', )
        parser.add_argument('--only', nargs='*', action='store', help='Show only listed column names. ', )
        parser.add_argument('--not', nargs='*', action='store', help='Show all columns except those listed.', )

        parser.add_argument('--long', '-l', action='store_true', help='Show full text: remove default substitutions.', )
        parser.add_argument('--sub-cols', nargs='*', action='store', default=['namespace', 'name', 'lookup_str'],
                            help='Columns for default substitutions. ', )
        parser.add_argument('--add', '-a', nargs=2, action='append', help='Add a substitution rule: regex, value.', )
        parser.add_argument('--cols', '-c', nargs='*', action='store', help='Columns used for added substitutions.', )

    # end def add_arguments

    def handle(self, *args, **kwargs):
        sys.stdout.write(str(args) + "\n")
        sys.stdout.write(str(kwargs) + "\n\n")
        sub_rules = [('^django.contrib', 'cb '), ('^django_registration', 'd_reg '), ('^django', '')]
        # sub_cols = ['namespace', 'name', 'lookup_str']
        sub_cols = kwargs.get('sub-cols', [])
        show_urls(sub_rules=sub_rules, sub_cols=sub_cols)

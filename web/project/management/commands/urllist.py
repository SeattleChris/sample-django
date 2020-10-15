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


def show_urls(mods=None, ignore=None, cols=None, sort=None, sub_rules=None):
    all_urls = collect_urls()
    if not all_urls:
        # sys.stdout.write("************* NO URLS FOUND *************")
        return ["************* NO URLS FOUND *************"]
    if sort:
        all_urls = sorted(all_urls, key=lambda x: [str(x[key] or '') for key in sort])
    title = {key: key for key in all_urls[0].keys()}
    if mods:
        mods.append('namespace')
    all_urls.append(title)
    remove_idx = []
    max_lengths = {}
    for i, u in enumerate(all_urls):
        for col in ['name', 'args']:
            val = u[col]
            u[col] = '' if val is None else str(val)
        # Prep removal, and don't compute width, for ignored modules or the known combo(s) that are long and unneeded.
        if u['namespace'] in ignore or (u['namespace'], u['name']) == ('admin', 'view_on_site'):
            remove_idx.append(i)
            continue
        if mods and u['namespace'] not in mods:
            remove_idx.append(i)
            continue
        if sub_rules:
            for regex, new_str, sub_cols in sub_rules:
                for col in sub_cols:
                    u[col] = re.sub(regex, new_str, u[col])
        for k, v in list(u.items())[:-1]:  # no ending border, so last column width not needed.
            u[k] = v = v or ''
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))
    for idx in reversed(remove_idx):
        all_urls.pop(idx)
    title = all_urls.pop()
    if len(cols) > 1:
        bar = {key: '*' * max_lengths.get(key, 4) for key in title}
        all_urls = [title, bar] + all_urls
    result = []
    for u in all_urls:
        result.append(' | '.join(
            ('{:%d}' % max_lengths.get(k, len(v))).format(v)
            for k, v in u.items() if k in cols
            ) + '\n')
    return result


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('modules', nargs='*', type=str, default=[],
                            help='Only show these listed modules. Default: show all.')
        # Optional Named Arguments: Rows (modules) and Columns (info about the url setting).
        parser.add_argument('--ignore', nargs='*', default=[], help='List of modules to ignore.', metavar='module')
        parser.add_argument('--only', nargs='*', help='Show only listed column names. ', metavar='col')
        parser.add_argument('--not', nargs='*', default=[], help='Show all columns except those listed.', metavar='col')
        parser.add_argument('--sort', nargs='*', default=['namespace', 'name'],  metavar='col',
                            help='Show all columns except those listed.',)
        # Optional Named Arguments: String substitutions for tighter view and readability.
        parser.add_argument('--long', '-l', action='store_true', help='Show full text: remove default substitutions.', )
        parser.add_argument('--sub-cols', nargs='*', action='store', default=['namespace', 'name', 'lookup_str'],
                            help='Columns for default substitutions. ', metavar='col', )
        parser.add_argument('--add', '-a', nargs=2, default=[], action='append', metavar=('regex', 'value', ),
                            help='Add a substitution rule: regex, value.', )
        parser.add_argument('--cols', '-c', nargs='*', help='Columns used for added substitutions.', metavar='col')
    # end def add_arguments

    def handle(self, *args, **kwargs):
        self.stdout.write(str(args) + "\n")
        self.stdout.write(str(kwargs) + "\n\n")
        mods = kwargs['modules']
        ignore = kwargs['ignore']
        self.stdout.write(str(mods) + "\n")
        self.stdout.write(str(ignore) + "\n")

        col_names = kwargs['only'] or ['namespace', 'name', 'pattern', 'lookup_str', 'args']
        col_names = [ea for ea in col_names if ea not in kwargs['not']]
        sc = kwargs.get('sub_cols', [])
        sub_rules = [('^django.contrib', 'cb ', sc), ('^django_registration', 'd_reg ', sc), ('^django', '', sc)]
        if kwargs['long']:
            sub_rules = []
        # cols = kwargs['cols'] or sc
        add_rules = [(*rule, kwargs['cols'] or sc) for rule in kwargs['add']]
        sub_rules.extend(add_rules)

        result = show_urls(mods=mods, ignore=ignore, cols=col_names, sort=kwargs['sort'], sub_rules=sub_rules)
        for row in result:
            self.stdout.write(row)

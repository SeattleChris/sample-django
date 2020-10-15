import re
from django.core.management import BaseCommand
from django.urls import resolvers


def collect_urls(urls=None, namespace=None, prefix=None):
    if urls is None:
        urls = resolvers.get_resolver()
    prefix = prefix or []
    if isinstance(urls, resolvers.URLResolver):
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
        return [{'namespace': namespace,
                 'name': urls.name,
                 'pattern': pattern,
                 'lookup_str': urls.lookup_str,
                 'args': dict(urls.default_args)}]
    else:
        raise ValueError(repr(urls))


def show_urls(mods=None, ignore=None, cols=None, sort=None, sub_rules=None):
    empty_value = "************* NO URLS FOUND *************"
    all_urls = collect_urls()
    if not all_urls:
        return empty_value
    if sort:
        all_urls = sorted(all_urls, key=lambda x: [str(x[key] or '') for key in sort])
    title = {key: key for key in all_urls[0].keys()}
    if mods:
        mods.append('namespace')
    all_urls.append(title)
    remove_idx, max_lengths = [], {}
    for i, u in enumerate(all_urls):
        for col in ['name', 'args']:
            val = u[col]
            u[col] = '' if val is None else str(val)
        # Prep removal, and don't compute length, for ignored modules or the known combo(s) that are long and unneeded.
        is_rejected = (u['namespace'], u['name']) == ('admin', 'view_on_site')
        if u['namespace'] in ignore or is_rejected or (mods and u['namespace'] not in mods):
            remove_idx.append(i)
            continue
        if sub_rules:
            for regex, new_str, sub_cols in sub_rules:
                for col in sub_cols:
                    u[col] = re.sub(regex, new_str, u[col])
        for k, v in list(u.items()):  # could skip last column length since there is no ending border.
            u[k] = v = v or ''
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))
    for idx in reversed(remove_idx):
        all_urls.pop(idx)
    if len(all_urls) == 1:
        return empty_value
    title = all_urls.pop()
    if len(cols) > 1:
        bar = {key: '*' * max_lengths.get(key, 4) for key in title}
        all_urls = [title, bar] + all_urls
    result = []
    for u in all_urls:
        result.append(' | '.join(('{:%d}' % max_lengths.get(k, len(v))).format(v) for k, v in u.items() if k in cols))
    # result = [' | '.join(('{:%d}' % max_lengths[k]).format(v) for k, v in u.items() if k in cols) for u in all_urls]
    return '\n'.join(result)


def get_sub_rules(kwargs):
    sc = kwargs.get('sub_cols', [])
    sub_rules = [('^django.contrib', 'cb ', sc), ('^django_registration', 'd_reg ', sc), ('^django', '', sc)]
    if kwargs['long']:
        sub_rules = []
    add_rules = [(*rule, kwargs['cols'] or sc) for rule in kwargs['add']]
    sub_rules.extend(add_rules)
    return sub_rules


def get_col_names(kwargs):
    col_names = kwargs['only'] or ['namespace', 'name', 'pattern', 'lookup_str', 'args']
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
        parser.add_argument('--sort', nargs='*', default=['namespace', 'name'],  metavar='col',
                            help='Sort by, in order of priority, column(s) value. Default: namespace name. ',)
        # Optional Named Arguments: String substitutions for tighter view and readability.
        parser.add_argument('--long', '-l', action='store_true', help='Show full text: remove default substitutions.', )
        parser.add_argument('--sub-cols', nargs='*', action='store', default=['namespace', 'name', 'lookup_str'],
                            help='Columns to apply the default substitutions. ', metavar='col', )
        parser.add_argument('--add', '-a', nargs=2, default=[], action='append', metavar=('regex', 'value', ),
                            help='Add a substitution rule: regex, value.', )
        parser.add_argument('--cols', '-c', nargs='*', metavar='col',
                            help='Columns to apply added substitutions. If none given, defaults to sub-cols. ', )

    def handle(self, *args, **kwargs):
        col_names = get_col_names(kwargs)
        sub_rules = get_sub_rules(kwargs)
        result = show_urls(kwargs['sources'], kwargs['ignore'], col_names, sort=kwargs['sort'], sub_rules=sub_rules)
        self.stdout.write(result)

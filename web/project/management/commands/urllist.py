import sys
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
        # sys.stdout.write("namespace: " + str(namespace) + "\n")
        # sys.stdout.write("")
        # sys.stdout.write(str(pattern))
        # sys.stdout.write("\n ----------------------- \n")
        return [{'namespace': namespace,
                 'name': urls.name,
                 'pattern': pattern,
                 'lookup_str': urls.lookup_str,
                 'args': dict(urls.default_args)}]
    else:
        raise ValueError(repr(urls))


def show_urls():
    all_urls = collect_urls()
    if not all_urls:
        sys.stdout.write("************* NO URLS FOUND *************")
        return
    title = {key: key for key in all_urls[0].keys()}
    all_urls.append(title)
    max_lengths = {}
    for u in all_urls:
        for k in ['args']:
            u[k] = str(u[k])
        for k in ['lookup_str']:
            u[k] = u[k]
        for k, v in list(u.items())[:-1]:  # no ending border, so last column width not needed.
            u[k] = v = v or ''
            # Skip app_list due to length (contains all app names)
            if (u['namespace'], u['name'], k) == ('admin', 'app_list', 'pattern'):
                continue
            max_lengths[k] = max(len(v), max_lengths.get(k, 0))
    heading_line = {key: '*'*max_lengths.get(key, 4) for key in title}
    all_urls = all_urls[-1:] + sorted(all_urls[:-1], key=lambda x: (x['namespace'], x['name']))
    for u in all_urls:
        sys.stdout.write(' | '.join(
            ('{:%d}' % max_lengths.get(k, len(v))).format(v)
            for k, v in u.items()) + '\n')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        show_urls()

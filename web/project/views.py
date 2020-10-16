from django.core.management import call_command
from django.shortcuts import render
from django.views.generic import TemplateView
import json


def home_view(request):
    urls = call_command('urllist', ignore=['admin'], only=['name'], long=True, data=True)
    context = {'all_urls': json.loads(urls)}
    return render(request, 'generic/home.html', context=context)


class NamedView(TemplateView):
    template_name = "generic/base.html"
    extra_context = {'css_sheets': ['css/home.css'], }

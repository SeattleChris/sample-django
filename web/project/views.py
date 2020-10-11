from django.shortcuts import render
from django.views.generic import TemplateView


def home_view(request):
    return render(request, 'generic/home.html')


class NamedView(TemplateView):
    template_name = "generic/base.html"
    extra_context = {'css_sheets': ['css/home.css'], }

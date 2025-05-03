from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.


def page_403(request, exception=None):
    return render(request, 'pages/403csrf.html', status=403)


def page_404(request, exception=None):
    return render(request, 'pages/404.html', status=404)


def page_500(request, exception=None):
    return render(request, 'pages/500.html', status=500)


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class RulesView(TemplateView):
    template_name = 'pages/rules.html'

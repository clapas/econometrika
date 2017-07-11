# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
import os
from django.shortcuts import render
from django.templatetags.static import static
from django.http import HttpResponse
from analysis.models import KeyValue, Plot

def non_normal_stock_returns(request):
    
    context = {'analysis_page': True}
    keys = [item for sublist in [['shapiro_wilk_test_W', 'shapiro_wilk_test_p']] + [prefix.join(\
        ['', '1pct,', '3pct,', '5pct,', '7pct,', '9pct,', '11pct']).split(',') for prefix in ['n_norm_drop_gt_', 'n_observed_drop_gt_', 'n_laplace_drop_gt_']]\
            for item in sublist]
    for k in keys:
        context[k] = KeyValue.objects.get(category='analysis.non_normal_stock_returns', key=k).value
    return render(request, 'analysis/non-normal-stock-returns.html', context)

def plot(request, name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    srcdoc = open(os.path.join(dir_path, 'static', 'analysis', '%s.html' % name), 'rb').read().decode('UTF-8')
    srcdoc = srcdoc.replace('plotly_lib', static('analysis/plotly_lib'))
    plot = Plot.objects.get(slug=name)
    title = plot.title
    print(title)
    html_above = plot.html_above
    return render(request, 'analysis/plot.html', {'srcdoc': srcdoc, 'title': title, 'html_above': html_above, 'plot_page': True})

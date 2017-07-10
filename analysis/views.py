# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
#from django.http import HttpResponse

def non_normal_stock_returns(request):
    from analysis.models import KeyValue
    
    context = {}
    keys = [item for sublist in [['shapiro_wilk_test_W', 'shapiro_wilk_test_p']] + [prefix.join(\
        ['', '1pct,', '3pct,', '5pct,', '7pct,', '9pct,', '11pct']).split(',') for prefix in ['n_norm_drop_gt_', 'n_observed_drop_gt_', 'n_laplace_drop_gt_']]\
            for item in sublist]
    for k in keys:
        context[k] = KeyValue.objects.get(category='analysis.non_normal_stock_returns', key=k).value
    return render(request, 'analysis/non-normal-stock-returns.html', context)

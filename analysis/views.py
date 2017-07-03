# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
#from django.http import HttpResponse

def index(request):
    context = {
        'shapiro_wilk_test_W': 0.93617,
        'shapiro_wilk_test_p': 2.2e-16

    }
    return render(request, 'analysis/non-normal-stock-returns.html', context)

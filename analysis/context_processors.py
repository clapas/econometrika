from analysis.models import Plot
from analysis.models import SymbolSearchForm

def menu(request):
    plots = Plot.objects.filter(type='statistic')
    context = {'plots' : plots, 'symbol_form': SymbolSearchForm}

    return context

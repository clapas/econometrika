from analysis.models import Plot

def menu(request):
    plots = Plot.objects.filter(type='statistic')
    context = {'plots' : plots}

    return context

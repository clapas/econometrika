from analysis.models import Plot

def menu(request):
    plots = Plot.objects.all()
    context = {'plots' : plots}

    return context

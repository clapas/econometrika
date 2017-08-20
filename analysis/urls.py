from django.conf.urls import url

from . import views
from analysis.views import SymbolAutocomplete

urlpatterns = [
    url(r'^$', views.non_normal_stock_returns, name='index'),
    url(r'^analysis/non-normal-stock-returns$', views.non_normal_stock_returns, name='non_normal_stock_returns'),
    url(r'^analysis/tolerance-limits$', views.stock_returns_tolerance_limits, name='stock_returns_tolerance_limits'),
    url(r'^plot/(?P<name>[.\w-]+)$', views.plot, name='plot'),
    url(r'^symbol-autocomplete/$', SymbolAutocomplete.as_view(), name='symbol-autocomplete',),
    url(r'^winners-losers$', views.winners_losers, name='winners_losers'),
]

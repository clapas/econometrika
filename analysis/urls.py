from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.non_normal_stock_returns, name='index'),
    #url(r'^analysis/$', views.non_normal_stock_returns, name='index'),
    url(r'^analysis/non_normal_stock_returns$', views.non_normal_stock_returns, name='non_normal_stock_returns'),
    url(r'^plot/(?P<name>[\w-]+)$', views.plot, name='plot')
]

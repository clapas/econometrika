from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.non_normal_stock_returns, name='index'),
    url(r'^non_normal_stock_returns$', views.non_normal_stock_returns, name='non_normal_stock_returns')
]
